# Echo Sorter 🎧

Echo Sorter is a powerful yet simple Django web application designed to bring order to your Spotify "Liked Songs." By authenticating with your Spotify account, the app automatically fetches all your liked tracks, sorts them into broad, easy-to-understand genre categories, and allows you to create new, organized playlists with a single click.

**Note:** This project is currently in local development, with plans for public deployment in the future.

***

## ✨ Key Features

* **Seamless Spotify Authentication**: Securely log in using your existing Spotify account with just one click.
* **Automatic Song Fetching**: The app automatically scans and fetches all the metadata for every track in your "Liked Songs" playlist.
* **Intelligent Genre Sorting**: Songs are sorted using a custom-built, broad genre mapping. For example, genres like *'alt-rock'*, *'punk'*, and *'classic rock'* are all grouped under the main **Rock** category.
* **One-Click Playlist Creation**: Once sorted, you can instantly create a new playlist on your Spotify account for any genre group.

***

## 🛠️ Tech Stack

* **Backend**: Python, Django
* **Frontend**: HTML, CSS, JavaScript
* **Database**: NoSQL
* **API**: [Spotipy](https://spotipy.readthedocs.io/en/2.22.1/) for the Spotify Web API

***
## 💡 How It Works

The application follows a simple but effective workflow:
1.  **Authentication**: It uses the **Spotipy** library to handle the Spotify OAuth 2.0 flow, allowing users to log in securely.
2.  **Data Fetching**: After authentication, it calls the Spotify API to retrieve the user's entire "Liked Songs" library, including detailed metadata for each track (artist, album, and associated genres).
3.  **Genre Mapping**: A custom logic layer processes the genre data for each track. It maps specific, niche genres to broader, more useful categories defined within the application.
4.  **Playlist Creation**: When a user requests a playlist, the app uses another API call to create a new public playlist in the user's Spotify account and adds all the relevant tracks to it.

## 🚀 Getting Started

This project is currently intended for local development. Follow these steps to get it running on your machine.

### Prerequisites

* Python 3.8+
* pip (Python package installer)
* A Spotify Developer account to get API credentials.

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone [https://github.com/akio-236/echo-sorter.git](https://github.com/akio-236/echo-sorter.git)
    cd echo-sorter
    ```

2.  **Create and activate a virtual environment:**
    * On macOS/Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```

3.  **Install dependencies:**
    *Create a `requirements.txt` file with the necessary packages (like Django and Spotipy) and install them.*
    ```sh
    pip install django spotipy
    # Add other dependencies as needed
    ```

4.  **Configure Spotify API Credentials:**
    * Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    * Create a new app to get your `Client ID` and `Client Secret`.
    * In the app settings on the dashboard, add a **Redirect URI**. For local development, this is typically `http://127.0.0.1:8000/callback` or a similar URL handled by your Django app.
    * Store these credentials securely. It is highly recommended to use environment variables instead of hardcoding them in your code. You can place them in your Django `settings.py` file for local testing:
        ```python
        # settings.py
        SPOTIPY_CLIENT_ID = 'YOUR_CLIENT_ID'
        SPOTIPY_CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
        SPOTIPY_REDIRECT_URI = '[http://127.0.0.1:8000/callback](http://127.0.0.1:8000/callback)' # Must match the one in your dashboard
        ```

5.  **Configure your Database:**
    * Set up your NoSQL database connection details in `settings.py`.

6.  **Run Django Migrations:**
    ```sh
    python manage.py migrate
    ```

7.  **Launch the Development Server:**
    ```sh
    python manage.py runserver
    ```
    The application should now be running at `http://127.0.0.1:8000`.

***

## 📋 Usage

1.  Open your web browser and navigate to `http://127.0.0.1:8000`.
2.  Click the "Login with Spotify" button and authorize the application.
3.  Once redirected, the app will display your liked songs sorted into genre groups.
4.  Find a genre group you want to create a playlist for and click the "Create Playlist" button next to it.
5.  Check your Spotify account—a new playlist with the sorted songs will be there!

***

## 🗺️ Roadmap & Future Plans

This project is actively being developed. Here are some of the planned features and improvements:

* **🚀 Public Deployment**: The primary goal is to deploy the application so anyone can use it without needing to run it locally.
* **🎨 UI/UX Enhancements**: Improve the user interface for a more intuitive and visually appealing experience.
* **🔧 Custom Genre Mapping**: Allow users to create, edit, and save their own broad genre mappings.
* **➕ Sort Other Playlists**: Extend the functionality to sort any of a user's existing playlists, not just "Liked Songs."
* **⚙️ Advanced Options**: Add options for creating private playlists and customizing playlist names and descriptions.

***

