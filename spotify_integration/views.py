import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import JsonResponse
import json
import os
from .genre_utils import BROAD_GENRE_MAPPING, map_specific_genres_to_broad

SCOPE = "user-library-read playlist-modify-public playlist-modify-private"


def get_spotify_auth():
    return SpotifyOAuth(
        client_id=settings.SPOTIPY_CLIENT_ID,
        client_secret=settings.SPOTIPY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
        cache_path="local_tokes.json",
    )


def auth_spotify(request):
    sp_oauth = get_spotify_auth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


def spotify_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")  # <--- Add this line to get potential error

    if error:  # <--- Check for an error first
        return JsonResponse(
            {"error": f"Spotify authorization error: {error}"}, status=400
        )

    if not code:  # <--- If no error and no code, then it's unexpected
        return JsonResponse(
            {
                "error": "No authorization code received (and no explicit error from Spotify)"
            },
            status=400,
        )

    sp_oauth = get_spotify_auth()

    try:
        token_info = sp_oauth.get_access_token(code)
        # You might want to save token_info securely (e.g., in a session)
        # request.session['token_info'] = token_info # Example: save token_info in session
        return redirect("spotify_integration:liked_songs")

    except Exception as e:
        return JsonResponse(
            {"error": f"Error during spotify callback: {e}"}, status=500
        )


def liked_songs(request):
    sp_oauth = get_spotify_auth()
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        print("No cached token found, redirecting to Spotify authorization.")
        return redirect("spotify_integration:auth_spotify")

    try:
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        liked_tracks = []
        all_artist_ids = set()  # To collect all unique artist IDs efficiently

        # Fetch all liked songs (with pagination)
        results = sp.current_user_saved_tracks(limit=50)
        while results:
            for item in results["items"]:
                track = item["track"]
                liked_tracks.append(
                    track
                )  # Store the full track object for later processing
                for artist in track["artists"]:
                    all_artist_ids.add(artist["id"])  # Collect artist IDs
            if results["next"]:
                results = sp.next(results)
            else:
                results = None

        print(f"Fetched {len(liked_tracks)} liked songs from Spotify.")
        print(f"Found {len(all_artist_ids)} unique artists.")

        # --- NEW: Fetch Artist Genres ---
        artist_genres_map = {}  # Map artist_id to their specific genres
        artist_ids_list = list(all_artist_ids)
        batch_size = 50  # Max artists per Spotify API call

        for i in range(0, len(artist_ids_list), batch_size):
            batch = artist_ids_list[i : i + batch_size]
            artists_details = sp.artists(batch)
            for artist_detail in artists_details["artists"]:
                if (
                    artist_detail
                ):  # Ensure artist_detail is not None (can happen if artist ID is bad)
                    artist_genres_map[artist_detail["id"]] = artist_detail.get(
                        "genres", []
                    )
        # --- END NEW: Fetch Artist Genres ---

        songs_data = []
        for track in liked_tracks:
            artists_names = []
            song_specific_genres = set()  # Collect specific genres for this song

            for artist in track["artists"]:
                artists_names.append(artist["name"])
                # Get specific genres from the map we just built
                specific_genres = artist_genres_map.get(artist["id"], [])
                for g in specific_genres:
                    song_specific_genres.add(g)

            # --- NEW: Map specific genres to broad genres ---
            broad_genres_for_song = map_specific_genres_to_broad(
                list(song_specific_genres)
            )
            # --- END NEW: Map specific genres to broad genres ---

            songs_data.append(
                {
                    "title": track["name"],
                    "artist": ", ".join(artists_names),
                    "album": track["album"]["name"],
                    "id": track["id"],
                    "preview_url": track["preview_url"],  # Useful for playing snippets
                    "image_url": track["album"]["images"][0]["url"]
                    if track["album"]["images"]
                    else "",
                    "broad_genres": broad_genres_for_song,  # ADDED: Broad genres for this song
                    # "specific_genres": list(song_specific_genres), # Optional: keep specific genres too
                }
            )

        print(f"Processed {len(songs_data)} songs with broad genres.")
        # For debugging, print first few songs with their broad genres
        # for song in songs_data[:5]:
        #     print(f"- {song['title']} by {song['artist']} | Genres: {song['broad_genres']}")

        return render(
            request, "spotify_integration/liked_songs.html", {"songs": songs_data}
        )

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 401:
            print(
                "Spotify API returned 401. Token might be expired or invalid. Clearing cache."
            )
            if os.path.exists("local_tokes.json"):
                os.remove("local_tokes.json")
            return redirect("spotify_integration:auth_spotify")
        print(f"Spotify API error: {e}")
        return JsonResponse({"error": f"Spotify API error: {e}"}, status=e.http_status)
    except Exception as e:
        print(f"An unexpected error occurred in liked_songs: {e}")
        return JsonResponse({"error": f"An unexpected error occurred: {e}"}, status=500)


def home(request):
    """Renders the home page with a Spotify connect button."""
    return render(request, "home.html")
