#!/bin/bash
# Script to rename files for Plex compatibility upon torrent completion
# Expected arguments from qBittorrent:
# $1: Content path (Full path to the torrent content)
# $2: Root path (Path where the torrent content is saved)
# $3: Save path (Absolute path to the torrent save location)
# $4: Torrent name
# $5: Category

CONTENT_PATH="$1"
ROOT_PATH="$2"
SAVE_PATH="$3"
TORRENT_NAME="$4"
CATEGORY="$5"

LOG_FILE="/config/plex_rename.log"

echo "----------------------------------------------------------------" >> "$LOG_FILE"
echo "Date: $(date)" >> "$LOG_FILE"
echo "Torrent Name: $TORRENT_NAME" >> "$LOG_FILE"
echo "Category: $CATEGORY" >> "$LOG_FILE"
echo "Content Path: $CONTENT_PATH" >> "$LOG_FILE"

# Only process if category matches typical media categories (optional)
# if [[ "$CATEGORY" != "movies" && "$CATEGORY" != "tv" ]]; then
#    echo "Skipping: Category not matched." >> "$LOG_FILE"
#    exit 0
# fi

# Function to sanitize filename for Plex
sanitize_name() {
    local name="$1"
    # Basic cleanup: remove common scene tags, replace dots with spaces, etc.
    # This is a simple example. For robust renaming, tools like FileBot or Radarr/Sonarr are better.
    # Here we just try to extract Title (Year).

    # 1. Replace dots with spaces
    cleaned_name="${name//./ }"

    # 2. Try to find year pattern (19xx or 20xx)
    if [[ $cleaned_name =~ (.*)[[:space:]]+\(([12][0-9]{3})\) ]]; then
        # Already has (Year) format? great.
        echo "$cleaned_name"
    elif [[ $cleaned_name =~ (.*)[[:space:]]+([12][0-9]{3}) ]]; then
        # Has Year but not in parens? Add them.
        title="${BASH_REMATCH[1]}"
        year="${BASH_REMATCH[2]}"
        echo "$title ($year)"
    else
        # Fallback: just return the cleaned name
        echo "$cleaned_name"
    fi
}

# Check if it's a single file or a directory
if [ -f "$CONTENT_PATH" ]; then
    echo "Processing single file..." >> "$LOG_FILE"
    DIR=$(dirname "$CONTENT_PATH")
    FILENAME=$(basename "$CONTENT_PATH")
    EXTENSION="${FILENAME##*.}"
    NAME_NO_EXT="${FILENAME%.*}"

    NEW_NAME=$(sanitize_name "$NAME_NO_EXT")
    NEW_FILENAME="${NEW_NAME}.${EXTENSION}"

    if [ "$FILENAME" != "$NEW_FILENAME" ]; then
        mv "$CONTENT_PATH" "$DIR/$NEW_FILENAME"
        echo "Renamed file: '$FILENAME' -> '$NEW_FILENAME'" >> "$LOG_FILE"
    else
        echo "No rename needed." >> "$LOG_FILE"
    fi

elif [ -d "$CONTENT_PATH" ]; then
    echo "Processing directory..." >> "$LOG_FILE"
    # For directories, we might want to rename the directory itself and/or video files inside
    DIR_NAME=$(basename "$CONTENT_PATH")
    NEW_DIR_NAME=$(sanitize_name "$DIR_NAME")

    # Rename directory if needed
    if [ "$DIR_NAME" != "$NEW_DIR_NAME" ]; then
        mv "$CONTENT_PATH" "$(dirname "$CONTENT_PATH")/$NEW_DIR_NAME"
        CONTENT_PATH="$(dirname "$CONTENT_PATH")/$NEW_DIR_NAME" # Update path
        echo "Renamed directory: '$DIR_NAME' -> '$NEW_DIR_NAME'" >> "$LOG_FILE"
    fi

    # Find and rename video files inside (simple approach)
    find "$CONTENT_PATH" -type f \( -name "*.mkv" -o -name "*.mp4" -o -name "*.avi" \) | while read -r FILE; do
        FILENAME=$(basename "$FILE")
        EXTENSION="${FILENAME##*.}"
        NAME_NO_EXT="${FILENAME%.*}"

        # Often the file inside already has a decent name or matches the folder,
        # but sometimes it's gibberish.
        # For simplicity, we'll apply the same sanitization or just ensure it matches the folder name logic.

        NEW_FILENAME_BASE=$(sanitize_name "$NAME_NO_EXT")
        new_file_path="$(dirname "$FILE")/$NEW_FILENAME_BASE.$EXTENSION"

        if [ "$FILE" != "$new_file_path" ]; then
             mv "$FILE" "$new_file_path"
             echo "Renamed file inside: '$FILENAME' -> '$NEW_FILENAME_BASE.$EXTENSION'" >> "$LOG_FILE"
        fi
    done
fi

echo "Done." >> "$LOG_FILE"
