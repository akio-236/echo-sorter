from django.urls import path
from . import views

app_name = "spotify_integration"

urlpatterns = [
    path("auth/", views.auth_spotify, name="auth_spotify"),
    path("callback/", views.spotify_callback, name="spotify_callback"),
    path("liked-songs/", views.liked_songs, name="liked_songs"),
]
