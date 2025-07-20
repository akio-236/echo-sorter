
import { useState, useEffect } from "react";
import { Music, Filter, RefreshCw, ExternalLink, User } from "lucide-react";
import { toast } from "sonner";
import SongCard from "../components/SongCard";
import GenreFilter from "../components/GenreFilter";
import CreatePlaylistButton from "../components/CreatePlaylistButton";
import SyncButton from "../components/SyncButton";

interface Song {
  id: string;
  name: string;
  artists: string[];
  album: string;
  album_cover?: string;
  preview_url?: string;
  genres: string[];
  spotify_url?: string;
}

const LikedSongs = () => {
  const [songs, setSongs] = useState<Song[]>([]);
  const [filteredSongs, setFilteredSongs] = useState<Song[]>([]);
  const [selectedGenre, setSelectedGenre] = useState<string>("all");
  const [availableGenres, setAvailableGenres] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock data for demonstration
  useEffect(() => {
    const mockSongs: Song[] = [
      {
        id: "1",
        name: "Blinding Lights",
        artists: ["The Weeknd"],
        album: "After Hours",
        album_cover: "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Pop", "R&B"],
        spotify_url: "https://open.spotify.com/track/0VjIjW4GlULA4LGvB9PmYV"
      },
      {
        id: "2",
        name: "Good 4 U",
        artists: ["Olivia Rodrigo"],
        album: "SOUR",
        album_cover: "https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bd89802e5a",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Pop", "Rock"],
        spotify_url: "https://open.spotify.com/track/4ZtFanR9U6ndgddUvNcjcG"
      },
      {
        id: "3",
        name: "Levitating",
        artists: ["Dua Lipa"],
        album: "Future Nostalgia",
        album_cover: "https://i.scdn.co/image/ab67616d0000b273fc915b69600616c2fb8164a0",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Pop", "Dance"],
        spotify_url: "https://open.spotify.com/track/463CkQjx2Zk1yXoBuierM9"
      },
      {
        id: "4",
        name: "Industry Baby",
        artists: ["Lil Nas X", "Jack Harlow"],
        album: "MONTERO",
        album_cover: "https://i.scdn.co/image/ab67616d0000b273be82673b5f79d9658ec0a9fd",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Hip-Hop", "Rap"],
        spotify_url: "https://open.spotify.com/track/27NovPIUIRrOZoCHxABJwK"
      },
      {
        id: "5",
        name: "Bad Habits",
        artists: ["Ed Sheeran"],
        album: "=",
        album_cover: "https://i.scdn.co/image/ab67616d0000b2732c2a9cf3e03bd5a6a46b78c9",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Pop"],
        spotify_url: "https://open.spotify.com/track/6YdB4ZkNwgJcJgWveOJg6w"
      },
      {
        id: "6",
        name: "Bohemian Rhapsody",
        artists: ["Queen"],
        album: "A Night at the Opera",
        album_cover: "https://i.scdn.co/image/ab67616d0000b273ce4f1737bc8a646c8c4bd25a",
        preview_url: "https://p.scdn.co/mp3-preview/...",
        genres: ["Rock", "Classic Rock"],
        spotify_url: "https://open.spotify.com/track/7tFiyTwD0nx5a1eklYtX2J"
      }
    ];

    // Simulate API call
    setTimeout(() => {
      setSongs(mockSongs);
      setFilteredSongs(mockSongs);
      
      // Extract unique genres
      const genres = [...new Set(mockSongs.flatMap(song => song.genres))];
      setAvailableGenres(genres);
      setLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    if (selectedGenre === "all") {
      setFilteredSongs(songs);
    } else {
      setFilteredSongs(songs.filter(song => song.genres.includes(selectedGenre)));
    }
  }, [selectedGenre, songs]);

  const handleCreatePlaylist = async (genre: string) => {
    try {
      // In a real app, this would make a POST request to /spotify/create_playlist/
      const response = await fetch('/spotify/create_playlist/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `genre=${encodeURIComponent(genre)}`
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Successfully created "${genre}" playlist!`, {
          description: "Opening playlist in Spotify...",
          action: {
            label: "Open",
            onClick: () => window.open(data.playlist_url, '_blank')
          }
        });
        
        // Simulate opening playlist and reloading
        setTimeout(() => {
          if (data.playlist_url) {
            window.open(data.playlist_url, '_blank');
          }
          window.location.reload();
        }, 1000);
      } else {
        throw new Error('Failed to create playlist');
      }
    } catch (error) {
      console.error('Error creating playlist:', error);
      toast.error("Failed to create playlist", {
        description: "Please try again or check your connection."
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-spotify-dark flex items-center justify-center">
        <div className="text-center space-y-4">
          <Music className="w-12 h-12 text-spotify-green animate-spin mx-auto" />
          <p className="text-spotify-light-gray">Loading your music library...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-spotify-dark">
      {/* Header */}
      <div className="bg-gradient-to-b from-spotify-green/20 to-transparent">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-spotify-white mb-2">
                Your Liked Songs
              </h1>
              <p className="text-spotify-light-gray">
                {songs.length} songs • Ready to organize by genre
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <SyncButton />
              <div className="flex items-center space-x-2 text-spotify-light-gray">
                <User className="w-4 h-4" />
                <span className="text-sm">Connected to Spotify</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="container mx-auto px-4 py-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0 mb-8">
          <GenreFilter
            genres={availableGenres}
            selectedGenre={selectedGenre}
            onGenreChange={setSelectedGenre}
          />
          
          {selectedGenre !== "all" && (
            <CreatePlaylistButton
              genre={selectedGenre}
              songCount={filteredSongs.length}
              onClick={handleCreatePlaylist}
            />
          )}
        </div>

        {/* Songs Grid */}
        {filteredSongs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredSongs.map((song) => (
              <SongCard key={song.id} song={song} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Music className="w-16 h-16 text-spotify-gray mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-spotify-white mb-2">
              No songs found
            </h3>
            <p className="text-spotify-light-gray">
              {selectedGenre === "all" 
                ? "Your liked songs will appear here once synced." 
                : `No songs found in the "${selectedGenre}" genre.`}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default LikedSongs;
