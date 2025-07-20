
import { Music, Headphones, Play } from "lucide-react";

const Home = () => {
  const handleSpotifyConnect = () => {
    // Redirect to Django backend Spotify auth endpoint
    window.location.href = '/spotify/auth/';
  };

  return (
    <div className="min-h-screen bg-spotify-dark flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-gradient-to-br from-spotify-green/20 via-transparent to-spotify-green/10"></div>
        <div 
          className="absolute inset-0" 
          style={{
            backgroundImage: `
              radial-gradient(circle at 20% 80%, rgba(29, 185, 84, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(29, 185, 84, 0.05) 0%, transparent 50%),
              radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.02) 0%, transparent 50%)
            `
          }}
        ></div>
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(45deg, transparent 40%, rgba(29, 185, 84, 0.02) 50%, transparent 60%),
              linear-gradient(-45deg, transparent 40%, rgba(179, 179, 179, 0.01) 50%, transparent 60%)
            `
          }}
        ></div>
      </div>

      <div className="max-w-md w-full text-center space-y-8 animate-fade-in relative z-10">
        {/* Logo and branding */}
        <div className="space-y-4">
          <div className="flex justify-center items-center space-x-2 mb-6">
            <div className="relative">
              <Music className="w-12 h-12 text-spotify-green" />
              <Headphones className="w-6 h-6 text-spotify-white absolute -bottom-1 -right-1" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-spotify-white mb-2">
            Echo<span className="text-spotify-green">Sorter</span>
          </h1>
          <p className="text-spotify-light-gray text-lg leading-relaxed">
            Transform your liked songs into genre-based playlists with the power of AI-driven music categorization
          </p>
        </div>

        {/* Features preview */}
        <div className="grid grid-cols-1 gap-4 py-6">
          <div className="flex items-center space-x-3 text-spotify-light-gray">
            <Play className="w-5 h-5 text-spotify-green" />
            <span>Connect your Spotify account</span>
          </div>
          <div className="flex items-center space-x-3 text-spotify-light-gray">
            <Music className="w-5 h-5 text-spotify-green" />
            <span>View and filter your liked songs</span>
          </div>
          <div className="flex items-center space-x-3 text-spotify-light-gray">
            <Headphones className="w-5 h-5 text-spotify-green" />
            <span>Create genre-based playlists</span>
          </div>
        </div>

        {/* Connect button */}
        <div className="space-y-4">
          <button
            onClick={handleSpotifyConnect}
            className="spotify-button w-full flex items-center justify-center space-x-2"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.481.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.42 1.56-.299.421-1.02.599-1.559.3z"/>
            </svg>
            <span>Connect with Spotify</span>
          </button>
          
          <p className="text-xs text-spotify-light-gray">
            Safe and secure. We only access your liked songs to help organize your music.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
