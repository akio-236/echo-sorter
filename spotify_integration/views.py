from datetime import timedelta, timezone
import os
import json
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from django.db import transaction
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Song, Artist, Album, SpecificGenre, BroadGenre, SpotifyToken
from .genre_utils import BROAD_GENRE_MAPPING, map_specific_genres_to_broad


logger = logging.getLogger(__name__)


def fetch_liked_songs_if_needed(user_id, sp):
    existing_songs = Song.objects.filter(user_id=user_id)
    if existing_songs.exists():
        logger.info(
            f"[CACHE HIT] Songs already exist for user {user_id}. Skipping fetch."
        )
        return False

    logger.info(f"[CACHE MISS] No songs for user {user_id}. Fetching from Spotify...")
    return True


def get_spotify_auth():
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-library-read playlist-modify-private playlist-modify-public",
    )


# Home page view
def home(request):
    """
    Renders the welcome page with the 'Connect with Spotify' button.
    """
    return render(request, "home.html")


# Spotify authentication initiation
def auth_spotify(request):
    """
    Redirects the user to Spotify's authorization page.
    """
    sp_oauth = get_spotify_auth()
    auth_url = sp_oauth.get_authorize_url()
    logger.info(f"Redirecting to Spotify authorization URL: {auth_url}")
    return redirect(auth_url)


def get_user_spotify_client(user_id):
    """
    Returns a Spotipy client for the given user_id.
    Refreshes token if expired.
    """
    try:
        token = SpotifyToken.objects.get(user_id=user_id)
    except SpotifyToken.DoesNotExist:
        return None

    # If token expired → refresh
    if token.expires_at <= timezone.now():
        sp_oauth = get_spotify_auth()
        refreshed_token = sp_oauth.refresh_access_token(token.refresh_token)

        token.access_token = refreshed_token["access_token"]
        token.expires_at = timezone.now() + timedelta(
            seconds=refreshed_token["expires_in"]
        )
        token.save(update_fields=["access_token", "expires_at"])

    return spotipy.Spotify(auth=token.access_token)


# Spotify Callback view for handling redirect after auth
def spotify_callback(request):
    """
    Handles the callback from Spotify after user authorization.
    Exchanges code for token, stores tokens per user in DB,
    fetches liked songs, and saves them to the local DB.
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
        # --- 1. Exchange authorization code for access + refresh tokens ---
        logger.info("Attempting to get Spotify access token...")
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        logger.info("Token obtained successfully.")

        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        expires_in = int(token_info["expires_in"])
        expires_at = timezone.now() + timedelta(seconds=expires_in)

        sp = spotipy.Spotify(auth=access_token)
        user_info = sp.current_user()
        user_id = user_info["id"]

        request.session["spotify_user_id"] = user_id

        expires_at = timezone.now() + timedelta(seconds=expires_in)
        SpotifyToken.objects.update_or_create(
            user_id=user_id,
            defaults={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at,
            },
        )

        # --- 3. Check whether to fetch liked songs ---
        should_fetch = fetch_liked_songs_if_needed(user_id, sp)
        if not should_fetch:
            return redirect("spotify_integration:liked_songs")

        logger.info(f"[SYNC] Starting data sync for user {user_id}...")

        # --- 4. Fetch all liked songs ---
        all_liked_tracks_spotify_ids = set()
        current_user_liked_tracks = []

        results = sp.current_user_saved_tracks(limit=50)
        while results:
            for item in results["items"]:
                track = item["track"]
                if track:
                    current_user_liked_tracks.append(track)
                    all_liked_tracks_spotify_ids.add(track["id"])
            results = sp.next(results) if results["next"] else None

        logger.info(
            f"[SYNC] Fetched {len(current_user_liked_tracks)} liked songs from Spotify API."
        )
        # Process and Save to DB within an atomic transaction
        with transaction.atomic():
            all_api_artist_ids = set()
            for track_data in current_user_liked_tracks:
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

            # Fetch detailed information for all unique artists in batches
            artist_details_from_api = {}
            artist_ids_list = list(all_api_artist_ids)
            batch_size = 50
            for i in range(0, len(artist_ids_list), batch_size):
                batch = artist_ids_list[i : i + batch_size]
                try:
                    artists_batch_details = sp.artists(batch)
                    for artist_detail in artists_batch_details["artists"]:
                        if artist_detail:  # Ensure artist_detail is not None
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

            # Save/Update Artists and their Specific Genres, then link to Broad Genres
            saved_artists = {}
            logger.info(
                "Processing artists and genres (logging only artists with no genres)..."
            )
            for artist_id, artist_data in artist_details_from_api.items():
                specific_genres_list = artist_data.get("genres", [])

                if not specific_genres_list:
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

                artist_obj.genres.clear()

                for specific_genre_name in specific_genres_list:
                    specific_genre_obj, created_sg = (
                        SpecificGenre.objects.get_or_create(name=specific_genre_name)
                    )

                    artist_obj.genres.add(specific_genre_obj)

                    broad_genres_for_specific = map_specific_genres_to_broad(
                        [specific_genre_name]
                    )
                    for broad_genre_name in broad_genres_for_specific:
                        broad_genre_obj, created_broad = (
                            BroadGenre.objects.get_or_create(name=broad_genre_name)
                        )
                        specific_genre_obj.broad_genres.add(broad_genre_obj)

            # Save/Update Albums and Songs, and link to Artists
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

                if not song_title:
                    logger.warning(f"Skipping song '{song_id}' due to missing title.")
                    continue

                if not album_data:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album data from Spotify."
                    )
                    continue

                album_name = album_data.get("name")
                if not album_name:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album name."
                    )
                    continue

                album_image_url = (
                    album_data["images"][0]["url"] if album_data.get("images") else None
                )
                if not album_image_url:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing album image URL."
                    )
                    continue

                if not artists_from_track:
                    logger.warning(
                        f"Skipping song '{song_title}' (ID: {song_id}) due to missing artist data."
                    )
                    continue

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
                        "preview_url": track_data.get("preview_url"),
                        "user_id": user_id,
                    },
                )
                if not created_song and song_obj.user_id != user_id:
                    song_obj.user_id = user_id
                    song_obj.save(update_fields=["user_id"])
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

                song_obj.artists.clear()
                for artist_data in artists_from_track:
                    artist_id = artist_data["id"]
                    if artist_id in saved_artists:
                        song_obj.artists.add(saved_artists[artist_id])
                    else:
                        logger.warning(
                            f"  Artist {artist_data['name']} (ID: {artist_id}) not found in batch cache for song {track_data['name']}. Creating minimally."
                        )
                        fallback_artist_obj, created_fb = Artist.objects.get_or_create(
                            spotify_id=artist_id, defaults={"name": artist_data["name"]}
                        )
                        song_obj.artists.add(fallback_artist_obj)

                processed_songs_spotify_ids.add(song_id)

            # Remove songs from DB that are no longer liked by the user OR were skipped during this run
            if request.GET.get("sync") == "true":
                db_current_songs = set(
                    Song.objects.values_list("spotify_id", flat=True)
                )
                songs_to_remove_ids = db_current_songs - processed_songs_spotify_ids
                if songs_to_remove_ids:
                    Song.objects.filter(spotify_id__in=songs_to_remove_ids).delete()
                    logger.info(
                        f"Removed {len(songs_to_remove_ids)} songs (no longer liked by user or skipped during sync) from DB."
                    )
                else:
                    logger.info(
                        "Skipping deletion of old songs because sync flag was not set."
                    )

        logger.info("[SYNC COMPLETE] Redirecting to liked songs page.")
        return redirect("spotify_integration:liked_songs")

    except spotipy.exceptions.SpotifyException as e:
        logger.error(f"Spotify API error during callback: {e}")
        if e.http_status == 401:
            logger.warning("Token expired or invalid. Removing stored token.")
            SpotifyToken.objects.filter(user_id=user_id).delete()
            return redirect("spotify_integration:auth_spotify")
        return JsonResponse({"error": f"Spotify API error: {e}"}, status=e.http_status)

    except Exception as e:
        logger.critical(
            f"An unexpected error occurred in spotify_callback: {e}", exc_info=True
        )
        return JsonResponse(
            {"error": f"An unexpected server error occurred: {e}"}, status=500
        )


# Liked Songs view
def liked_songs(request):
    """
    Displays the user's liked songs from the local database.
    Uses DB-backed token management (no local cache).
    """
    # Resolve Spotify user ID from session
    spotify_user_id = request.session.get("spotify_user_id")
    if not spotify_user_id:
        logger.info("[LIKED_SONGS] No Spotify user in session, redirecting for auth.")
        return redirect("spotify_integration:auth_spotify")

    # Get Spotify client for this user
    sp = get_user_spotify_client(spotify_user_id)
    if not sp:
        logger.info("[LIKED_SONGS] No valid Spotify token, redirecting for auth.")
        return redirect("spotify_integration:auth_spotify")

    # Pull songs for this user from local DB
    songs_data = []
    songs_from_db = (
        Song.objects.filter(user_id=spotify_user_id)
        .select_related("album")
        .prefetch_related("artists__genres")
        .order_by("title")
    )

    logger.debug(
        f"[LIKED_SONGS] Preparing to process {len(songs_from_db)} songs for template."
    )

    for song_obj in songs_from_db:
        artists_names = [artist.name for artist in song_obj.artists.all()]
        broad_genres_for_song = song_obj.broad_genres

        # Debug logging for problematic records
        if (
            not song_obj.album
            or not song_obj.album.image_url
            or not broad_genres_for_song
        ):
            logger.debug(
                f"[LIKED_SONGS:ISSUE] Song '{song_obj.title}' (ID: {song_obj.spotify_id})\n"
                f"  Album: {song_obj.album.name if song_obj.album else 'N/A'}\n"
                f"  Image URL: {song_obj.album.image_url if song_obj.album else 'N/A'}\n"
                f"  Artists: {', '.join(artists_names)}\n"
                f"  Broad Genres: {broad_genres_for_song}\n" + "-" * 40
            )

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
                "broad_genres": broad_genres_for_song,
            }
        )

    logger.debug(
        f"[LIKED_SONGS] Successfully prepared {len(songs_data)} songs for template render."
    )

    # Build unique genre filter list
    all_available_broad_genres = {
        genre for song_item in songs_data for genre in song_item["broad_genres"]
    }
    sorted_broad_genres = sorted(list(all_available_broad_genres))

    # Render template
    return render(
        request,
        "spotify_integration/liked_songs.html",
        {
            "songs": songs_data,
            "broad_genres_for_filter": sorted_broad_genres,
        },
    )


@csrf_exempt
@require_POST
def create_playlist(request):
    """
    Creates a new Spotify playlist for the given genre and populates it with
    all songs mapped to that genre from the local DB.
    Uses DB-backed token management (multi-user ready).
    """
    genre = request.POST.get("genre", "").strip().lower()
    if not genre:
        return JsonResponse({"error": "Genre not provided"}, status=400)

    # --- 1. Resolve Spotify user ---
    spotify_user_id = request.session.get("spotify_user_id")
    if not spotify_user_id:
        logger.info(
            "[CREATE_PLAYLIST] No Spotify user in session, redirecting for auth."
        )
        return redirect("spotify_integration:auth_spotify")

    # --- 2. Get Spotify client for this user ---
    sp = get_user_spotify_client(spotify_user_id)
    if not sp:
        logger.info("[CREATE_PLAYLIST] No valid Spotify token, redirecting for auth.")
        return redirect("spotify_integration:auth_spotify")

    # --- 3. Create playlist in Spotify ---
    playlist_name = f"{genre.title()} Playlist"
    playlist = sp.user_playlist_create(
        user=spotify_user_id, name=playlist_name, public=False
    )
    playlist_id = playlist["id"]

    # --- 4. Collect songs of this genre from DB (for this user only) ---
    genre_songs = (
        Song.objects.prefetch_related("artists__genres__broad_genres")
        .filter(
            artists__genres__broad_genres__name__iexact=genre, user_id=spotify_user_id
        )
        .distinct()
    )

    logger.debug(f"[CREATE_PLAYLIST] Requested genre: '{genre}'")
    logger.debug(
        f"[CREATE_PLAYLIST] Found {genre_songs.count()} songs with genre '{genre}'"
    )

    track_uris = [f"spotify:track:{song.spotify_id}" for song in genre_songs]

    # --- 5. Add songs to playlist in batches (Spotify limit = 100) ---
    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist_id, track_uris[i : i + 100])

    return JsonResponse(
        {
            "message": f"Playlist '{playlist_name}' created with {len(track_uris)} songs!",
            "playlist_url": playlist.get("external_urls", {}).get("spotify", ""),
        }
    )
