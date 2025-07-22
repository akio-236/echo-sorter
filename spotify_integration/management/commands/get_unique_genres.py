import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import os


class Command(BaseCommand):
    help = "Fetches all unique genres from artists associated with liked songs and prints them."

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "Ensure you have authenticated with Spotify via the web interface at least once."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "This command requires a cached token ('local_tokes.json')."
            )
        )

        sp_oauth = SpotifyOAuth(
            client_id=settings.SPOTIPY_CLIENT_ID,
            client_secret=settings.SPOTIPY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIPY_REDIRECT_URI,
            scope="user-library-read",  # Only need this scope
            cache_path="local_tokes.json",  # Ensure this matches where your token is saved
        )

        token_info = sp_oauth.get_cached_token()

        if not token_info:
            raise CommandError(
                "No cached Spotify token found. Please run your Django app in the browser, "
                "connect with Spotify, and complete the authentication flow first. "
                f"Then run this command again. Authorization URL: {sp_oauth.get_authorize_url()}"
            )

        sp = spotipy.Spotify(auth_manager=sp_oauth)

        self.stdout.write(
            self.style.SUCCESS("Fetching liked songs and collecting artist IDs...")
        )
        all_unique_artist_ids = set()

        results = sp.current_user_saved_tracks(limit=50)  # Start with 50 tracks
        while results:
            for item in results["items"]:
                track = item["track"]
                for artist in track["artists"]:
                    all_unique_artist_ids.add(artist["id"])
            if results["next"]:
                results = sp.next(results)  # Go to next page of results
            else:
                results = None  # No more pages

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {len(all_unique_artist_ids)} unique artists from your liked songs."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Fetching genres for these artists (this might take a moment if you have many unique artists)..."
            )
        )

        all_unique_genres = set()
        artist_ids_list = list(all_unique_artist_ids)
        batch_size = 50  # Spotify API allows up to 50 artists per request

        for i in range(0, len(artist_ids_list), batch_size):
            batch = artist_ids_list[i : i + batch_size]
            try:
                artists_details = sp.artists(batch)
                for artist_detail in artists_details["artists"]:
                    if artist_detail and "genres" in artist_detail:
                        for genre in artist_detail["genres"]:
                            all_unique_genres.add(genre)
            except spotipy.exceptions.SpotifyException as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"Error fetching artist details for batch (index {i}): {e}"
                    )
                )
                if e.http_status == 401:
                    raise CommandError(
                        "Spotify token expired or invalid during artist fetch. Please re-authenticate your app in the browser and try again."
                    )
                # Continue processing other batches even if one fails
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(
                        f"An unexpected error occurred while processing artist batch (index {i}): {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n--- Found {len(all_unique_genres)} Unique Specific Genres ---"
            )
        )
        sorted_genres = sorted(list(all_unique_genres))
        for genre in sorted_genres:
            self.stdout.write(genre)

        self.stdout.write(
            self.style.SUCCESS(
                "\nCopy the list above. Use it to manually define your BROAD_GENRE_MAPPING dictionary."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Remember to turn your firewall back on after getting the genres!"
            )
        )
