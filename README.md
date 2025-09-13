# Echo Sorter 🎧

Echo Sorter is a powerful yet simple Django web application designed to bring order to your Spotify "Liked Songs." By authenticating with your Spotify account, the app automatically fetches all your liked tracks, sorts them into broad, easy-to-understand genre categories, and allows you to create new, organized playlists with a single click.

**Note:** This project is currently in local development, with plans for public deployment in the future.

***

## ✨ Key Features

* **Seamless Spotify Authentication**: Securely log in using your existing Spotify account with just one click.
* **Automatic Song Fetching**: The app automatically scans and fetches all the metadata for every track in your "Liked Songs" playlist.
* **Intelligent Genre Sorting**: Songs are sorted using a custom-built, broad genre mapping.
* **One-Click Playlist Creation**: Instantly create a new, organized playlist on your Spotify account for any genre group.

***
## 🛠️ Tech Stack

* **Backend**: Python, Django
* **Frontend**: HTML, CSS, JavaScript
* **Database**: NoSQL
* **API**: [Spotipy](https://spotipy.readthedocs.io/en/2.22.1/) for the Spotify Web API

***

## 💡 How It Works

1.  **Authentication**: Uses **Spotipy** to handle the Spotify OAuth 2.0 flow for secure login.
2.  **Data Fetching**: After authentication, it calls the Spotify API to retrieve the user's "Liked Songs" library.
3.  **Genre Mapping**: A custom logic layer processes the genre data for each track, mapping specific genres to broader categories.
4.  **Playlist Creation**: On user request, it uses another API call to create a new playlist and add all relevant tracks.

***

## 📸 Screenshots

Here is a preview of the application's main pages.

### Home Page
The main landing page that allows a user to log in with their Spotify account.
<img width="1857" height="940" alt="image" src="https://github.com/user-attachments/assets/058615a7-6ca6-433b-80bd-f71329be7ba5" />


### Liked Songs Page
After logging in, this page displays your liked songs sorted into genre groups, with a button to create a playlist for each category.
<img width="1848" height="931" alt="image" src="https://github.com/user-attachments/assets/42bd7377-4bbb-4929-a997-6992eb213e56" />

***



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
    *Create a `requirements.txt` file with the necessary packages and install them.*
    ```sh
    pip install django spotipy
    # Add other dependencies as needed
    ```

4.  **Configure Spotify API Credentials:**
    * Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
    * Create a new app to get your `Client ID` and `Client Secret`.
    * In the app settings on the dashboard, add a **Redirect URI**. For local development, this is typically `http://127.0.0.1:8000/callback`.
    * Store these credentials securely in your Django `settings.py` file:
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
2.  On the **Home Page**, click the "Login with Spotify" button and authorize the application.
3.  You will be redirected to the **Liked Songs Page**, which will display your sorted genre groups.
4.  Click the "Create Playlist" button next to any genre to instantly add that playlist to your Spotify account.

***

## 🗺️ Roadmap & Future Plans

This project is actively being developed. Here are some of the planned features and improvements:

* **🚀 Public Deployment**: The primary goal is to deploy the application so anyone can use it without needing to run it locally.
* **🎨 UI/UX Enhancements**: Improve the user interface for a more intuitive and visually appealing experience.
* **🔧 Custom Genre Mapping**: Allow users to create, edit, and save their own broad genre mappings.
* **➕ Sort Other Playlists**: Extend the functionality to sort any of a user's existing playlists, not just "Liked Songs."
* **⚙️ Advanced Options**: Add options for creating private playlists and customizing playlist names and descriptions.

***

