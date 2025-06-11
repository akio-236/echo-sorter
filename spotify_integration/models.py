from django.db import models


class BroadGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SpecificGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    broad_genres = models.ManyToManyField(BroadGenre, related_name="specific_genres")

    def __str__(self):
        return self.name


class Artist(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    genres = models.ManyToManyField(
        SpecificGenre, related_name="artists"
    )  # Specific Spotify genres

    def __str__(self):
        return self.name


class Album(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    image_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(selfself):
        return self.name


class Song(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=250)
    artists = models.ManyToManyField(Artist, related_name="songs")
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="songs")
    preview_url = models.URLField(max_length=500, blank=True, null=True)
    # You don't store broad_genres directly here, as they are derived from artists' specific genres.
    # But you could add a computed property or method to get them.

    def __str__(self):
        return self.title

    @property
    def broad_genres(self):
        # This property calculates broad genres on the fly based on associated artists
        from .genre_utils import (
            map_specific_genres_to_broad,
        )  # Import here to avoid circular dependency

        all_specific_genres = set()
        for artist in self.artists.all():
            for specific_genre in artist.genres.all():
                all_specific_genres.add(specific_genre.name)
        return map_specific_genres_to_broad(list(all_specific_genres))
