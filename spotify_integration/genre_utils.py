BROAD_GENRE_MAPPING = {
    # This will be populated based on the list you provide to me
    # Example:
    # "Rock": ["alternative rock", "punk rock", "classic rock"],
    # "Pop": ["indie pop", "dance pop"],
    # ...
}


def map_specific_genres_to_broad(specific_genres):
    """
    Maps a list of specific Spotify genres to a list of broad genres
    using the BROAD_GENRE_MAPPING.
    """
    broad_genres = set()
    for specific_genre in specific_genres:
        # Iterate through the mapping to find matching broad genres
        for broad_category, specific_genre_list in BROAD_GENRE_MAPPING.items():
            if specific_genre in specific_genre_list:
                broad_genres.add(broad_category)
    return sorted(list(broad_genres))
