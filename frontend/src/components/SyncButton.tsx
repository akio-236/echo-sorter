
import { RefreshCw } from "lucide-react";

const SyncButton = () => {
  const handleSync = () => {
    window.location.href = '/spotify/callback/?sync=true';
  };

  return (
    <button
      onClick={handleSync}
      className="flex items-center space-x-2 text-spotify-light-gray hover:text-spotify-white transition-colors duration-200 text-sm"
      title="Sync songs again"
    >
      <RefreshCw className="w-4 h-4" />
      <span>Sync Songs Again</span>
    </button>
  );
};

export default SyncButton;
