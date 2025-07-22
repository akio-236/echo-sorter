from django.db import models


class BroadGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class SpecificGenre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # Ensure related_name is correct here
    broad_genres = models.ManyToManyField(
        BroadGenre, related_name="specific_genres_link"
    )  # Changed related_name for clarity and uniqueness

    def __str__(self):
        return self.name


class Artist(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    # Ensure related_name is correct here
    genres = models.ManyToManyField(
        SpecificGenre, related_name="artists_link"
    )  # Changed related_name for clarity and uniqueness

    def __str__(self):
        return self.name


class Album(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    image_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name


class Song(models.Model):
    spotify_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=250)
    # Ensure related_name is correct here
    artists = models.ManyToManyField(
        Artist, related_name="songs_link"
    )  # Changed related_name for clarity and uniqueness
    album = models.ForeignKey(
        Album, on_delete=models.CASCADE, related_name="songs_on_album"
    )  # Changed related_name
    preview_url = models.URLField(max_length=500, blank=True, null=True)
    user_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def broad_genres(self):
        # Import here to avoid circular dependency issues when models.py is loaded
        from .genre_utils import map_specific_genres_to_broad

        all_specific_genres = set()
        # Iterate through artists related to this song
        for artist in self.artists.all():
            # Iterate through specific genres related to each artist
            for specific_genre in artist.genres.all():
                all_specific_genres.add(specific_genre.name)
        return map_specific_genres_to_broad(list(all_specific_genres))
