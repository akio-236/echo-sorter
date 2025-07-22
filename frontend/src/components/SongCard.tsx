
import { ExternalLink, Play } from "lucide-react";

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

interface SongCardProps {
  song: Song;
}

const SongCard = ({ song }: SongCardProps) => {
  const handlePreviewClick = () => {
    if (song.preview_url) {
      window.open(song.preview_url, '_blank');
    } else if (song.spotify_url) {
      window.open(song.spotify_url, '_blank');
    }
  };

  return (
    <div className="song-card group">
      {/* Album Cover */}
      <div className="relative mb-4">
        <img
          src={song.album_cover || '/placeholder.svg'}
          alt={`${song.album} cover`}
          className="w-full aspect-square object-cover rounded-lg"
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/placeholder.svg';
          }}
        />
        
        {/* Play button overlay */}
        {(song.preview_url || song.spotify_url) && (
          <button
            onClick={handlePreviewClick}
            className="absolute bottom-2 right-2 bg-spotify-green hover:bg-spotify-green/90 text-white p-2 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110"
            title="Preview on Spotify"
          >
            {song.preview_url ? (
              <Play className="w-4 h-4" fill="currentColor" />
            ) : (
              <ExternalLink className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Song Info */}
      <div className="space-y-2">
        <h3 className="font-semibold text-spotify-white text-sm leading-tight line-clamp-2">
          {song.name}
        </h3>
        
        <p className="text-spotify-light-gray text-xs line-clamp-1">
          {song.artists.join(', ')}
        </p>
        
        <p className="text-spotify-light-gray text-xs line-clamp-1">
          {song.album}
        </p>

        {/* Genre Tags */}
        <div className="flex flex-wrap gap-1 mt-3">
          {song.genres.slice(0, 2).map((genre) => (
            <span key={genre} className="genre-tag">
              {genre}
            </span>
          ))}
          {song.genres.length > 2 && (
            <span className="genre-tag">
              +{song.genres.length - 2}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default SongCard;
