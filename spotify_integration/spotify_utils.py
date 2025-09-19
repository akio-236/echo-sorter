from echosorter_project import settings
import spotipy
from django.utils import timezone
from spotipy.oauth2 import SpotifyOAuth
from datetime import timedelta
from .models import SpotifyToken
from .views import get_spotify_auth


def get_spotify_auth():
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-library-read playlist-modify-private playlist-modify-public",
    )


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
