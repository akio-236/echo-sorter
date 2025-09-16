# Echo Sorter: AI Coding Agent Instructions

## Project Overview

Echo Sorter is a Django web app that organizes Spotify "Liked Songs" by genre and enables one-click playlist creation. It uses Spotipy for Spotify API integration and custom genre mapping logic.

## Architecture & Key Components

- **Backend:**
  - Django project in `echosorter_project/` (settings, URLs, WSGI/ASGI)
  - Main app: `spotify_integration/` (models, views, genre logic, admin, tests)
  - Management commands in `spotify_integration/management/commands/`
  - Migrations in `spotify_integration/migrations/`
- **Frontend:**
  - Templates in `templates/` (home, liked songs)
  - Static assets in `static/` and `staticfiles/`
- **Database:**
  - Default is SQLite (`db.sqlite3`), but README mentions NoSQL plans.
- **External Integration:**
  - Spotipy for Spotify OAuth and API calls
  - Credentials set in `settings.py` (see README for details)

## Developer Workflows

- **Setup:**
  - Use Python 3.8+, create a virtual environment, install dependencies from `requirements.txt`
  - Add Spotify API credentials to `settings.py`
- **Run:**
  - `python manage.py migrate` (apply migrations)
  - `python manage.py runserver` (start dev server)
- **Testing:**
  - Tests are in `spotify_integration/tests.py`
  - Run with `python manage.py test spotify_integration`
- **Custom Commands:**
  - Management commands (e.g., `get_unique_genres.py`) can be run via `python manage.py <command>`

## Project-Specific Patterns & Conventions

- **Genre Mapping:**
  - Custom logic in `spotify_integration/genre_utils.py` maps Spotify genres to broad categories.
- **Spotify Integration:**
  - OAuth and API handled in `spotify_integration/views.py` and `genre_utils.py`
- **Templates:**
  - Use Django template inheritance; main user flows are in `home.html` and `liked_songs.html`
- **Static Files:**
  - Place images, CSS, JS in `static/` and `staticfiles/` (admin assets in subfolders)
- **Settings:**
  - Store sensitive credentials in environment variables or directly in `settings.py` (see README)

## Integration Points

- **Spotipy:**
  - Used for all Spotify API interactions (auth, fetching songs, creating playlists)
- **Django ORM:**
  - Models in `spotify_integration/models.py` for storing user, song, and genre data

## Example Workflow

1. User logs in via Spotify (OAuth handled by Spotipy)
2. App fetches liked songs, processes genres, displays sorted results
3. User clicks to create a playlist; app uses Spotipy to create and populate it

## References

- `README.md`: Setup, architecture, and usage details
- `echosorter_project/settings.py`: Configuration, credentials
- `spotify_integration/genre_utils.py`: Genre mapping logic
- `spotify_integration/views.py`: Main business logic
- `spotify_integration/tests.py`: Test cases
- `templates/`: UI templates

---

**Feedback:** If any section is unclear or missing, please specify which workflows, patterns, or integration details need further documentation.
