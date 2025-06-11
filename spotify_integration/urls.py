# spotify_integration/urls.py

from django.urls import path
from . import views  # Import views from the current app

app_name = "spotify_integration"  # This is important for namespacing URLs

urlpatterns = [
    path(
        "auth/", views.auth_spotify, name="auth_spotify"
    ),  # This was likely your original auth path
    path("callback/", views.spotify_callback, name="spotify_callback"),
    path("liked_songs/", views.liked_songs, name="liked_songs"),
    # Add other paths specific to your spotify_integration app here if needed
]
