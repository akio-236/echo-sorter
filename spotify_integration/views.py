import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import JsonResponse
import json
import os

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
    sp_oauth = (
        get_spotify_auth()
    )  # This correctly initializes SpotifyOAuth with cache_path

    # Attempt to get the token from the cache.
    # get_cached_token() will return token_info if available and not expired beyond refresh window.
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        # If no token is cached (e.g., first visit, or cache cleared), redirect for re-authorization.
        print("No cached token found, redirecting to Spotify authorization.")
        return redirect("spotify_integration:auth_spotify")

    try:
        # Initialize Spotify client using the SpotifyOAuth object as the auth_manager.
        # This is the idiomatic way; Spotipy will automatically use/refresh the token from the cache.
        sp = spotipy.Spotify(auth_manager=sp_oauth)

        liked_tracks = []
        # Fetching liked songs
        results = sp.current_user_saved_tracks()
        liked_tracks.extend(results["items"])

        while results["next"]:
            results = sp.next(results)
            liked_tracks.extend(results["items"])

        songs_data = []
        for item in liked_tracks:
            track = item["track"]
            artists = ", ".join([artist["name"] for artist in track["artists"]])
            songs_data.append(
                {
                    "title": track["name"],
                    "artist": artists,
                    "album": track["album"]["name"],
                    "id": track["id"],
                }
            )

        print(f"Fetched {len(songs_data)} liked songs from Spotify")
        for song in songs_data[:10]:
            print(f"- {song['title']} by {song['artist']}")

        return render(
            request, "spotify_integration/liked_songs.html", {"songs": songs_data}
        )

    except spotipy.exceptions.SpotifyException as e:
        # This handles cases where Spotify returns an error,
        # often due to an invalid/expired token that couldn't be refreshed.
        if e.http_status == 401:  # Unauthorized
            print(
                "Spotify API returned 401. Token might be expired or invalid. Clearing cache."
            )
            # Clear the cache file to force a fresh re-authentication.
            # You refer to the literal filename passed during SpotifyOAuth instantiation.
            if os.path.exists("local_tokes.json"):
                os.remove("local_tokes.json")
            return redirect("spotify_integration:auth_spotify")
        # For other Spotify API errors, return a JSON response with the error details.
        print(f"Spotify API error: {e}")
        return JsonResponse({"error": f"Spotify API error: {e}"}, status=e.http_status)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred in liked_songs: {e}")
        return JsonResponse({"error": f"An unexpected error occurred: {e}"}, status=500)


def home(request):
    """Renders the home page with a Spotify connect button."""
    return render(request, "home.html")
