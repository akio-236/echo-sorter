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
    if not code:
        return JsonResponse({"error": "No authorization code received"}, status=400)
    sp_oauth = get_spotify_auth()

    try:
        token_info = sp_oauth.get_access_token(code)
        return redirect("spotify_integration: liked_songs")

    except Exception as e:
        return JsonResponse(
            {"error": f"Error during spotify callback: {e}"}, status=500
        )


def liked_songs(request):
    sp_oauth = get_spotify_auth()
    token_info = sp_oauth.validate_token(sp_oauth.cahce_path)

    if not token_info:
        return redirect("spotify_integration: auth_spotify")

    try:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        liked_tracks = []
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

    except Exception as e:
        if isinstance(e, spotipy.exceptions.SpotifyException) and e.http_status == 401:
            if os.path.exists(sp_oauth.cache_path):
                os.remove(sp_oauth.cache_path)
            return redirect("spotify_integration: auth_spotify")
        return JsonResponse({"error": f"Error fetching liked songs: {e}"}, status=500)
