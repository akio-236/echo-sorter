
import { Plus, Music } from "lucide-react";

interface CreatePlaylistButtonProps {
  genre: string;
  songCount: number;
  onClick: (genre: string) => void;
}

const CreatePlaylistButton = ({ genre, songCount, onClick }: CreatePlaylistButtonProps) => {
  return (
    <button
      onClick={() => onClick(genre)}
      className="spotify-button flex items-center space-x-2"
      disabled={songCount === 0}
    >
      <Plus className="w-4 h-4" />
      <Music className="w-4 h-4" />
      <span>Create {genre} Playlist ({songCount})</span>
    </button>
  );
};

export default CreatePlaylistButton;
