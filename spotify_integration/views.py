# F:\Projects\echo-sorter\spotify_integration\views.py

import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from django.db import transaction  # Crucial for atomic database operations
import logging  # For better logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone

# Configure a logger for this module
logger = logging.getLogger(__name__)

# Import your models
from .models import Song, Artist, Album, SpecificGenre, BroadGenre

# Import your genre mapping utilities
from .genre_utils import BROAD_GENRE_MAPPING, map_specific_genres_to_broad


# --- Helper function for Spotify Authentication ---
def get_spotify_auth():
    """
    Initializes and returns a SpotifyOAuth object.
    Uses 'local_tokes.json' for token caching.
    """
    redirect_uri = settings.SPOTIPY_REDIRECT_URI
    logger.debug(f"SPOTIPY_REDIRECT_URI for auth: {redirect_uri}")

    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=redirect_uri,
        scope="user-library-read user-read-private user-read-email playlist-modify-private playlist-modify-public",
        cache_path="local_tokes.json",  # Path to store cached tokens
    )


# --- View for the Home Page ---
def home(request):
    """
    Renders the welcome page with the 'Connect with Spotify' button.
    """
    return render(request, "home.html")


# --- View to initiate Spotify Authorization ---
def auth_spotify(request):
    """
    Redirects the user to Spotify's authorization page.
    """
    sp_oauth = get_spotify_auth()
    auth_url = sp_oauth.get_authorize_url()
    logger.info(f"Redirecting to Spotify authorization URL: {auth_url}")
    return redirect(auth_url)


# --- Spotify Callback View (Handles the redirect from Spotify) ---
def spotify_callback(request):
    """
    Handles the callback from Spotify after user authorization.
    Exchanges code for token, fetches liked songs, and saves to DB.
    Includes logic to skip songs with critical missing metadata.
    """
    sp_oauth = get_spotify_auth()
    code = request.GET.get("code")

    if not code:
        error_message = request.GET.get("error", "No authorization code received.")
        logger.error(f"Spotify callback failed: {error_message}")
        return JsonResponse(
            {"error": f"Spotify authorization failed: {error_message}"}, status=400
        )

    try:
        # Exchange authorization code for an access token
        logger.info("Attempting to get Spotify access token...")
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        logger.info("Token obtained and cached successfully.")

        sp = spotipy.Spotify(auth_manager=sp_oauth)

        # --- Start Data Sync to Database ---
        logger.info("Starting data sync to database...")
        all_liked_tracks_spotify_ids = (
            set()
        )  # To track Spotify IDs of currently liked songs
        current_user_liked_tracks = []  # Store full track objects from Spotify

        # Fetch all liked songs from Spotify API with pagination
        results = sp.current_user_saved_tracks(limit=50)
        while results:
            for item in results["items"]:
                track = item["track"]
                if track:  # Ensure track data exists
                    current_user_liked_tracks.append(track)
                    all_liked_tracks_spotify_ids.add(track["id"])
            if results["next"]:
                results = sp.next(results)
            else:
                results = None

        logger.info(
            f"Fetched {len(current_user_liked_tracks)} liked songs from Spotify API."
        )

        # Process and Save to DB within an atomic transaction
        with transaction.atomic():
            # Step 1: Collect all unique artist IDs from the fetched liked songs
            all_api_artist_ids = set()
            for track_data in current_user_liked_tracks:
                # Only add artists if track_data is valid enough to attempt processing later
                song_id = track_data.get("id")
                song_title = track_data.get("name")
                album_data = track_data.get("album")
                album_image_url = (
                    album_data["images"][0]["url"]
                    if album_data and album_data.get("images")
                    else None
                )
                artists_from_track = track_data.get("artists", [])

                # Only add artists to the batch fetch if the song has critical data
                if (
                    song_title
                    and album_data
                    and album_data.get("name")
                    and album_image_url
                    and artists_from_track
                ):
                    for artist_data in artists_from_track:
                        all_api_artist_ids.add(artist_data["id"])
                else:
                    logger.warning(
                        f"Skipping artist ID collection for song '{song_title}' (ID: {song_id}) due to critical missing metadata."
                    )

            logger.info(
                f"Collected {len(all_api_artist_ids)} unique artist IDs for genre fetching."
            )

            # Step 2: Fetch detailed information (including genres) for all unique artists in batches
            artist_details_from_api = {}  # Dictionary to store artist_id -> artist_detail
            artist_ids_list = list(all_api_artist_ids)
            batch_size = 50  # Spotify API allows up to 50 artist IDs per request
            for i in range(0, len(artist_ids_list), batch_size):
                batch = artist_ids_list[i : i + batch_size]
                try:
                    artists_batch_details = sp.artists(batch)
                    for artist_detail in artists_batch_details["artists"]:
                        if artist_detail:  # Ensure artist_detail is not None (can happen if artist ID is invalid)
                            artist_details_from_api[artist_detail["id"]] = artist_detail
                except spotipy.exceptions.SpotifyException as e:
                    logger.warning(
                        f"Spotify API error fetching artist details for batch (skipping {i}-{i + batch_size - 1}): {e}"
                    )
                except Exception as e:
                    logger.error(
                        f"Unexpected error fetching artist details for batch (skipping {i}-{i + batch_size - 1}): {e}"
                    )

            logger.info(
                f"Fetched details for {len(artist_details_from_api)} artists from Spotify API for genre parsing."
            )

            # Step 3: Save/Update Artists and their Specific Genres, then link to Broad Genres
            saved_artists = {}  # Cache Artist objects to avoid repeated DB queries during song processing
            logger.info(
                "Processing artists and genres (logging only artists with no genres)..."
            )
            for artist_id, artist_data in artist_details_from_api.items():
                specific_genres_list = artist_data.get("genres", [])

                if (
                    not specific_genres_list
                ):  # Conditional logging: ONLY PRINT DEBUG FOR ARTISTS WITH NO GENRES
                    logger.debug(
                        f"  Processing Artist (No Genres Found): {artist_data['name']} (ID: {artist_id})"
                    )
                    logger.debug(
                        f"    Specific genres from Spotify API: {specific_genres_list}"
                    )

                artist_obj, created = Artist.objects.get_or_create(
                    spotify_id=artist_id, defaults={"name": artist_data["name"]}
                )
                if not created and artist_obj.name != artist_data["name"]:
                    artist_obj.name = artist_data["name"]
                    artist_obj.save(update_fields=["name"])
                saved_artists[artist_id] = artist_obj

                # Clear existing specific genres for artists to resync their genres from Spotify
                artist_obj.genres.clear()

                for specific_genre_name in specific_genres_list:
                    specific_genre_obj, created_sg = (
                        SpecificGenre.objects.get_or_create(name=specific_genre_name)
                    )

                    artist_obj.genres.add(specific_genre_obj)

                    # Link SpecificGenre to BroadGenre using your defined mapping
                    broad_genres_for_specific = map_specific_genres_to_broad(
                        [specific_genre_name]
                    )
                    for broad_genre_name in broad_genres_for_specific:
                        broad_genre_obj, created_broad = (
                            BroadGenre.objects.get_or_create(name=broad_genre_name)
                        )
                        specific_genre_obj.broad_genres.add(broad_genre_obj)

            # Step 4: Save/Update Albums and Songs, and link to Artists
            logger.info(
                "Processing songs and albums (logging only problematic ones that are skipped)..."
            )
            processed_songs_spotify_ids = (
                set()
            )  # Track songs actually processed and saved
            for track_data in current_user_liked_tracks:
                song_id = track_data.get("id")
                song_title = track_data.get("name")
                album_data = track_data.get("album")
                artists_from_track = track_data.get("artists", [])

                # --- CRITICAL MISSING DATA CHECKS - SKIPPING SONGS ---
                if not song_title:
                    logger.warning(f"Skipping song '{song_id}' due to missing title.")
                    continue  # Skip to the next song

                if not album_data:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album data from Spotify."
                    )
                    continue  # Skip to the next song

                album_name = album_data.get("name")
                if not album_name:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album name."
                    )
                    continue  # Skip to the next song

                album_image_url = (
                    album_data["images"][0]["url"] if album_data.get("images") else None
                )
                if not album_image_url:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album image URL."
                    )
                    continue  # Skip to the next song

                if not artists_from_track:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing artist data."
                    )
                    continue  # Skip to the next song
                # --- END CRITICAL MISSING DATA CHECKS ---

                album_obj, created_album = Album.objects.get_or_create(
                    spotify_id=album_data["id"],
                    defaults={"name": album_data["name"], "image_url": album_image_url},
                )
                if not created_album:
                    updated_album_fields = []
                    if album_obj.name != album_data["name"]:
                        album_obj.name = album_data["name"]
                        updated_album_fields.append("name")
                    if album_obj.image_url != album_image_url:
                        album_obj.image_url = album_image_url
                        updated_album_fields.append("image_url")
                    if updated_album_fields:
                        album_obj.save(update_fields=updated_album_fields)

                song_obj, created_song = Song.objects.get_or_create(
                    spotify_id=track_data["id"],
                    defaults={
                        "title": track_data["name"],
                        "album": album_obj,
                        "preview_url": track_data.get(
                            "preview_url"
                        ),  # Use .get() for safety
                    },
                )
                if not created_song:
                    updated_song_fields = []
                    if song_obj.title != track_data["name"]:
                        song_obj.title = track_data["name"]
                        updated_song_fields.append("title")
                    if song_obj.album != album_obj:
                        song_obj.album = album_obj
                        updated_song_fields.append("album")
                    if song_obj.preview_url != track_data.get("preview_url"):
                        song_obj.preview_url = track_data.get("preview_url")
                        updated_song_fields.append("preview_url")
                    if updated_song_fields:
                        song_obj.save(update_fields=updated_song_fields)

                # Link artists to the song's ManyToMany field
                song_obj.artists.clear()  # Clear existing artists to resync relationships
                for artist_data in (
                    artists_from_track
                ):  # Use artists_from_track which was checked for emptiness
                    artist_id = artist_data["id"]
                    if artist_id in saved_artists:
                        song_obj.artists.add(saved_artists[artist_id])
                    else:
                        # Fallback: if an artist wasn't in the initial batch fetch (e.g., API error for that artist),
                        # create them here minimally to maintain the song-artist link.
                        logger.warning(
                            f"  Artist {artist_data['name']} (ID: {artist_id}) not found in batch cache for song {track_data['name']}. Creating minimally."
                        )
                        fallback_artist_obj, created_fb = Artist.objects.get_or_create(
                            spotify_id=artist_id, defaults={"name": artist_data["name"]}
                        )
                        song_obj.artists.add(fallback_artist_obj)

                processed_songs_spotify_ids.add(
                    song_id
                )  # Add to the set of actually processed songs

            # Remove songs from DB that are no longer liked by the user OR were skipped during this run
            # This ensures only successfully processed songs remain in the DB
            db_current_songs = set(Song.objects.values_list("spotify_id", flat=True))
            songs_to_remove_ids = db_current_songs - processed_songs_spotify_ids
            if songs_to_remove_ids:
                Song.objects.filter(spotify_id__in=songs_to_remove_ids).delete()
                logger.info(
                    f"Removed {len(songs_to_remove_ids)} songs (no longer liked by user or skipped during sync) from DB."
                )

        logger.info("Data sync complete. Redirecting to liked songs page.")
        # --- End Data Sync to Database ---

        return redirect("spotify_integration:liked_songs")

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error during callback: {e}")
        if e.http_status == 401:
            logger.warning(
                "Token expired or invalid. Clearing cache to force re-authentication."
            )
            # Ensure local_tokes.json is in your project root or accessible
            if os.path.exists("local_tokes.json"):
                os.remove("local_tokes.json")
            return redirect(
                "spotify_integration:auth_spotify"
            )  # Redirect to re-authenticate
        return JsonResponse({"error": f"Spotify API error: {e}"}, status=e.http_status)
    except Exception as e:
        logger.critical(
            f"An unexpected error occurred in spotify_callback: {e}", exc_info=True
        )
        return JsonResponse(
            {"error": f"An unexpected server error occurred: {e}"}, status=500
        )


# The 'liked_songs' view code would follow here (it's unchanged for this request)


# --- Liked Songs Display View ---
def liked_songs(request):
    """
    Displays the user's liked songs from the local database.
    """
    sp_oauth = get_spotify_auth()
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        logger.info("No cached Spotify token found, redirecting for authentication.")
        return redirect("spotify_integration:auth_spotify")

    songs_data = []

    # Optimize query: select_related for ForeignKey (album), prefetch_related for ManyToMany (artists)
    # This will fetch related data in a minimal number of queries.
    songs_from_db = (
        Song.objects.select_related("album")
        .prefetch_related("artists__genres")
        .all()
        .order_by("title")
    )
    # ^ Added __genres to prefetch related genres for artists as well, making broad_genres property more efficient

    logger.debug(
        f"DEBUG_LIKED_SONGS: Preparing to process {len(songs_from_db)} songs for template (logging only problematic ones)."
    )

    for song_obj in songs_from_db:
        artists_names = []
        for artist in song_obj.artists.all():
            artists_names.append(artist.name)

        # The broad_genres property will compute genres based on artists' specific genres
        broad_genres_for_song = song_obj.broad_genres

        # Condition to trigger debug prints for songs with issues
        has_issue = False
        if not song_obj.album or not song_obj.album.image_url:
            has_issue = True  # Missing album or image
        if not broad_genres_for_song:  # If broad_genres_for_song is an empty list
            has_issue = True  # No broad genres found for the song

        if has_issue:
            logger.debug(
                f"DEBUG_LIKED_SONGS: Processing Song with Issue: '{song_obj.title}' (ID: {song_obj.spotify_id})"
            )
            logger.debug(
                f"  Album Name: {song_obj.album.name if song_obj.album else 'N/A'}"
            )
            logger.debug(
                f"  Image URL: {song_obj.album.image_url if song_obj.album else 'N/A'}"
            )
            logger.debug(f"  Artists: {', '.join(artists_names)}")
            logger.debug(
                f"  Broad Genres computed by property: {broad_genres_for_song}"
            )
            logger.debug("-" * 40)  # Separator for readability

        songs_data.append(
            {
                "title": song_obj.title,
                "artist": ", ".join(artists_names)
                if artists_names
                else "Various Artists",
                "album": song_obj.album.name if song_obj.album else "N/A",
                "id": song_obj.spotify_id,
                "preview_url": song_obj.preview_url,
                "image_url": song_obj.album.image_url
                if song_obj.album and song_obj.album.image_url
                else "/static/default_album_art.png",
                "broad_genres": broad_genres_for_song,  # This is a list of strings
            }
        )
    logger.debug(
        f"DEBUG_LIKED_SONGS: Successfully prepared {len(songs_data)} songs for template render."
    )

    # Get unique broad genres from all songs to populate the filter dropdown
    all_available_broad_genres = set()
    for song_item in songs_data:
        for genre in song_item["broad_genres"]:
            all_available_broad_genres.add(genre)

    sorted_broad_genres = sorted(list(all_available_broad_genres))

    return render(
        request,
        "spotify_integration/liked_songs.html",
        {
            "songs": songs_data,
            "broad_genres_for_filter": sorted_broad_genres,  # Pass sorted genres for the filter
        },
    )


@csrf_exempt
@require_POST
def create_playlist(request):
    genre = request.POST.get("genre", "").strip().lower()
    if not genre:
        return JsonResponse({"error": "Genre not provided"}, status=400)

    sp_oauth = get_spotify_auth()
    token_info = sp_oauth.get_cached_token()
    if not token_info:
        return redirect("spotify_integration:auth_spotify")

    sp = spotipy.Spotify(auth=token_info["access_token"])

    user = sp.current_user()
    user_id = user["id"]

    playlist_name = f"{genre} Playlist ({timezone.now().strftime('%Y-%m-%d')})"
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=False)
    playlist_id = playlist["id"]

    # Case-insensitive match
    genre_songs = (
        Song.objects.prefetch_related("artists__genres__broad_genres")
        .filter(artists__genres__broad_genres__name__iexact=genre)
        .distinct()
    )

    print(f"[DEBUG] Requested genre: '{genre}'")
    print(f"[DEBUG] Found {genre_songs.count()} songs with genre '{genre}'")

    track_uris = [f"spotify:track:{song.spotify_id}" for song in genre_songs]

    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i : i + 100])

    return JsonResponse(
        {
            "message": f"Playlist '{playlist_name}' created with {len(track_uris)} songs!",
            "playlist_url": playlist["external_urls"]["spotify"],
        }
    )
