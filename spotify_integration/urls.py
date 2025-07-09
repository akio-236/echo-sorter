# spotify_integration/urls.py

from django.urls import path
from . import views  # Import views from the current app

app_name = "spotify_integration"  # This is important for namespacing URLs

urlpatterns = [
    path("", views.home, name="home"),
    path("auth/", views.auth_spotify, name="auth_spotify"),
    path("callback/", views.spotify_callback, name="spotify_callback"),
    path("liked_songs/", views.liked_songs, name="liked_songs"),
    path("create_playlist/", views.create_playlist, name="create_playlist"),
]
