
import { Filter } from "lucide-react";

interface GenreFilterProps {
  genres: string[];
  selectedGenre: string;
  onGenreChange: (genre: string) => void;
}

const GenreFilter = ({ genres, selectedGenre, onGenreChange }: GenreFilterProps) => {
  return (
    <div className="flex items-center space-x-3">
      <div className="flex items-center space-x-2 text-spotify-light-gray">
        <Filter className="w-4 h-4" />
        <span className="text-sm font-medium">Filter by genre:</span>
      </div>
      
      <select
        value={selectedGenre}
        onChange={(e) => onGenreChange(e.target.value)}
        className="bg-spotify-gray text-spotify-white px-4 py-2 rounded-lg border-none focus:outline-none focus:ring-2 focus:ring-spotify-green text-sm min-w-32"
      >
        <option value="all">All Genres</option>
        {genres.map((genre) => (
          <option key={genre} value={genre}>
            {genre}
          </option>
        ))}
      </select>
    </div>
  );
};

export default GenreFilter;
