import os
import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from django.db import transaction  # For atomic database operations

# Import your new models
from .models import Song, Artist, Album, SpecificGenre, BroadGenre

# Import your genre mapping utilities
from .genre_utils import BROAD_GENRE_MAPPING, map_specific_genres_to_broad


def home(request):
    """
    Renders the main welcome page.
    """
    return render(request, "home.html")


# --- Your existing get_spotify_auth function (should remain the same) ---
def get_spotify_auth():
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope="user-library-read user-read-private user-read-email",  # Ensure user-library-read is included
        cache_path="local_tokes.json",
    )


# --- Your existing auth_spotify function (should remain the same) ---
def auth_spotify(request):
    sp_oauth = get_spotify_auth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


# --- MODIFIED: spotify_callback function ---
def spotify_callback(request):
    sp_oauth = get_spotify_auth()
    code = request.GET.get("code")

    if code:
        try:
            # Exchange authorization code for an access token
            # check_cache=False ensures we always get a fresh token if callback is hit
            token_info = sp_oauth.get_access_token(code, check_cache=False)
            print("Token obtained and cached successfully.")

            sp = spotipy.Spotify(auth_manager=sp_oauth)

            # --- Start Data Sync to Database ---
            print("Starting data sync to database...")
            all_liked_tracks_spotify_ids = (
                set()
            )  # To track Spotify IDs of currently liked songs
            current_user_liked_tracks = []  # Store full track objects from Spotify

            # Fetch all liked songs from Spotify API with pagination
            results = sp.current_user_saved_tracks(limit=50)
            while results:
                for item in results["items"]:
                    track = item["track"]
                    current_user_liked_tracks.append(track)
                    all_liked_tracks_spotify_ids.add(track["id"])
                if results["next"]:
                    results = sp.next(results)
                else:
                    results = None

            print(
                f"Fetched {len(current_user_liked_tracks)} liked songs from Spotify API."
            )

            # Process and Save to DB within an atomic transaction
            # This ensures that if any part of the save fails, the entire transaction is rolled back,
            # preventing partial or corrupted data.
            with transaction.atomic():
                # Step 1: Collect all unique artist IDs from the fetched liked songs
                all_api_artist_ids = set()
                for track_data in current_user_liked_tracks:
                    for artist_data in track_data["artists"]:
                        all_api_artist_ids.add(artist_data["id"])
                print(
                    f"Collected {len(all_api_artist_ids)} unique artist IDs from liked songs for genre fetching."
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
                                artist_details_from_api[artist_detail["id"]] = (
                                    artist_detail
                                )
                    except spotipy.exceptions.SpotifyException as e:
                        # Log error but continue processing other batches
                        print(
                            f"Warning: Spotify API error fetching artist details for batch (skipping {i}-{i + batch_size - 1}): {e}"
                        )
                    except Exception as e:
                        print(
                            f"Warning: Unexpected error fetching artist details for batch (skipping {i}-{i + batch_size - 1}): {e}"
                        )

                print(
                    f"Fetched details for {len(artist_details_from_api)} artists from Spotify API for genre parsing."
                )

                # Step 3: Save/Update Artists and their Specific Genres, then link to Broad Genres
                saved_artists = {}  # Cache Artist objects to avoid repeated DB queries during song processing
                for artist_id, artist_data in artist_details_from_api.items():
                    print(
                        f"  Processing Artist: {artist_data['name']} (ID: {artist_id})"
                    )
                    artist_obj, created = Artist.objects.get_or_create(
                        spotify_id=artist_id, defaults={"name": artist_data["name"]}
                    )
                    if not created and artist_obj.name != artist_data["name"]:
                        artist_obj.name = artist_data["name"]
                        artist_obj.save(update_fields=["name"])
                        print(f"    Updated existing Artist: {artist_obj.name}")
                    elif created:
                        print(f"    Created new Artist: {artist_obj.name}")
                    else:
                        print(f"    Found existing Artist: {artist_obj.name}")
                    saved_artists[artist_id] = artist_obj

                    # Clear existing specific genres for artists to resync their genres from Spotify
                    artist_obj.genres.clear()
                    specific_genres_list = artist_data.get("genres", [])
                    print(
                        f"    Specific genres for {artist_data['name']}: {specific_genres_list}"
                    )
                    for specific_genre_name in specific_genres_list:
                        # Get or create the SpecificGenre
                        specific_genre_obj, created_sg = (
                            SpecificGenre.objects.get_or_create(
                                name=specific_genre_name
                            )
                        )
                        if created_sg:
                            print(
                                f"      Created new SpecificGenre: {specific_genre_obj.name}"
                            )

                        # Add the specific genre to the artist's genres
                        artist_obj.genres.add(specific_genre_obj)

                        # Link SpecificGenre to BroadGenre using your defined mapping
                        broad_genres_for_specific = map_specific_genres_to_broad(
                            [specific_genre_name]
                        )
                        for broad_genre_name in broad_genres_for_specific:
                            # Get or create the BroadGenre
                            broad_genre_obj, created_broad = (
                                BroadGenre.objects.get_or_create(name=broad_genre_name)
                            )
                            if created_broad:
                                print(
                                    f"        Created new BroadGenre: {broad_genre_obj.name}"
                                )
                            # Add the broad genre to the specific genre's broad_genres (ManyToMany)
                            specific_genre_obj.broad_genres.add(broad_genre_obj)
                            print(
                                f"        Linked '{specific_genre_obj.name}' to broad genre '{broad_genre_obj.name}'"
                            )
                    if not specific_genres_list:
                        print(
                            f"    No specific genres found for Artist: {artist_data['name']}"
                        )

                # Step 4: Save/Update Albums and Songs, and link to Artists
                print("Processing songs and albums...")
                for track_data in current_user_liked_tracks:
                    album_data = track_data["album"]
                    # Get the largest available image URL for the album art
                    album_image_url = (
                        album_data["images"][0]["url"] if album_data["images"] else None
                    )

                    print(
                        f"  Processing Album: {album_data['name']} (ID: {album_data['id']})"
                    )
                    # Get or create the Album instance
                    album_obj, created_album = Album.objects.get_or_create(
                        spotify_id=album_data["id"],
                        defaults={
                            "name": album_data["name"],
                            "image_url": album_image_url,
                        },
                    )
                    # Update album details if it already exists and has changed
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
                            print(
                                f"    Updated existing Album: {album_obj.name} ({', '.join(updated_album_fields)})"
                            )
                        else:
                            print(
                                f"    Found existing Album: {album_obj.name} (no updates needed)"
                            )
                    else:
                        print(f"    Created new Album: {album_obj.name}")

                    print(
                        f"  Processing Song: {track_data['name']} (ID: {track_data['id']})"
                    )
                    # Get or create the Song instance
                    song_obj, created_song = Song.objects.get_or_create(
                        spotify_id=track_data["id"],
                        defaults={
                            "title": track_data["name"],
                            "album": album_obj,
                            "preview_url": track_data["preview_url"],
                        },
                    )
                    # Update song details if it already exists and has changed
                    if not created_song:
                        updated_song_fields = []
                        if song_obj.title != track_data["name"]:
                            song_obj.title = track_data["name"]
                            updated_song_fields.append("title")
                        if song_obj.album != album_obj:
                            song_obj.album = album_obj
                            updated_song_fields.append("album")
                        if song_obj.preview_url != track_data["preview_url"]:
                            song_obj.preview_url = track_data["preview_url"]
                            updated_song_fields.append("preview_url")
                        if updated_song_fields:
                            song_obj.save(update_fields=updated_song_fields)
                            print(
                                f"    Updated existing Song: {song_obj.title} ({', '.join(updated_song_fields)})"
                            )
                        else:
                            print(
                                f"    Found existing Song: {song_obj.title} (no updates needed)"
                            )
                    else:
                        print(f"    Created new Song: {song_obj.title}")

                    # Link artists to the song's ManyToMany field
                    song_obj.artists.clear()  # Clear existing artists to resync relationships
                    for artist_data in track_data["artists"]:
                        artist_id = artist_data["id"]
                        if artist_id in saved_artists:
                            # Use the Artist object we already created/cached
                            song_obj.artists.add(saved_artists[artist_id])
                            print(
                                f"      Linked Artist '{artist_data['name']}' to Song '{song_obj.title}'"
                            )
                        else:
                            # Fallback: if an artist wasn't in the initial batch fetch (e.g., API error for that artist),
                            # create them here minimally to maintain the song-artist link.
                            # Their genres might be missing, but the song will still be linked.
                            print(
                                f"      Warning: Artist {artist_data['name']} (ID: {artist_id}) not found in batch cache for song {track_data['name']}. Fetching/creating minimally."
                            )
                            fallback_artist_obj, created_fb = (
                                Artist.objects.get_or_create(
                                    spotify_id=artist_id,
                                    defaults={"name": artist_data["name"]},
                                )
                            )
                            song_obj.artists.add(fallback_artist_obj)
                            if created_fb:
                                print(
                                    f"        Created fallback Artist: {fallback_artist_obj.name}"
                                )
                            # Note: Genres for fallback artists won't be fetched here to avoid more API calls.
                            # A full resync would fix their genres later.

                # Optional: Remove songs from DB that are no longer liked by the user
                # This keeps your local database clean and in sync with the user's Spotify library.
                db_liked_song_ids = set(
                    Song.objects.values_list("spotify_id", flat=True)
                )
                songs_to_remove_ids = db_liked_song_ids - all_liked_tracks_spotify_ids
                if songs_to_remove_ids:
                    Song.objects.filter(spotify_id__in=songs_to_remove_ids).delete()
                    print(
                        f"Removed {len(songs_to_remove_ids)} songs no longer liked by the user from DB."
                    )

            print("Data sync complete. Redirecting to liked songs page.")
            # --- End Data Sync to Database ---

            # Redirect to the liked songs page after successful sync
            return redirect("spotify_integration:liked_songs")

        except spotipy.exceptions.SpotifyException as e:
            # Handle Spotify API specific errors (e.g., token expiration, invalid scope)
            print(f"Spotify API error during callback: {e}")
            if e.http_status == 401:
                print(
                    "Token expired or invalid. Clearing cache to force re-authentication."
                )
                if os.path.exists("local_tokes.json"):
                    os.remove("local_tokes.json")
                return redirect(
                    "spotify_integration:auth_spotify"
                )  # Redirect to re-authenticate
            return JsonResponse(
                {"error": f"Spotify API error: {e}"}, status=e.http_status
            )
        except Exception as e:
            # Handle any other unexpected errors
            print(f"An unexpected error occurred in spotify_callback: {e}")
            # Consider logging the full traceback for unhandled exceptions
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {"error": f"An unexpected server error occurred: {e}"}, status=500
            )


# --- MODIFIED: liked_songs function ---
def liked_songs(request):
    sp_oauth = get_spotify_auth()
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        # If no token, prompt user to connect (or refresh if needed)
        return redirect("spotify_integration:auth_spotify")

    songs_data = []

    # --- MODIFIED: Load songs from the database in a more optimized way ---
    # Fetch songs without prefetching all nested relationships at once
    # We will fetch related data in separate queries or through attribute access later.
    songs_from_db = Song.objects.all().order_by("title")

    # Prefetch albums separately as they are a ForeignKey (simpler relation)
    # This reduces complexity compared to prefetching M2M chains
    # If the Album object was causing the issue, fetching it this way might help.
    songs_from_db = songs_from_db.select_related("album")

    # Fetch artists and their genres separately
    # This avoids the deep join created by 'artists__genres__broad_genres' in a single query
    # and will fetch artists for all songs in an efficient batch.
    # The 'artists' relationship on Song is ManyToMany, so prefetch_related is good for it.
    songs_from_db = songs_from_db.prefetch_related("artists")

    # Now iterate through songs and fetch artist-genres-broad_genres as needed
    # Django's ORM usually handles caching, so repeated access to artists.all()
    # won't necessarily hit the DB repeatedly if artists were prefetched.
    # The broad_genres property on Song will handle the mapping.

    for song_obj in songs_from_db:
        artists_names = []
        for artist in song_obj.artists.all():
            artists_names.append(artist.name)
            # The broad_genres property on the Song model itself correctly calculates this
            # by accessing artist.genres.all() which in turn accesses SpecificGenre's broad_genres
            # This is where the potential depth is, but accessing it per song is usually okay.

        # Access the broad_genres property from the Song model
        broad_genres_for_song = (
            song_obj.broad_genres
        )  # This property will internally query/use cached data

        songs_data.append(
            {
                "title": song_obj.title,
                "artist": ", ".join(artists_names),
                "album": song_obj.album.name,
                "id": song_obj.spotify_id,
                "preview_url": song_obj.preview_url,
                "image_url": song_obj.album.image_url,
                "broad_genres": broad_genres_for_song,
            }
        )
    print(f"Loaded {len(songs_data)} songs from the database.")
    # --- End Load from DB ---

    return render(
        request, "spotify_integration/liked_songs.html", {"songs": songs_data}
    )
