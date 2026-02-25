#!/bin/bash
# Smart Rename Script for Plex
# $1: Content path, $2: Root path, $3: Save path, $4: Torrent name, $5: Category

CONTENT_PATH="$1"
SAVE_PATH="$3"
TORRENT_NAME="$4"
CATEGORY="$5"

LOG_FILE="/config/plex_rename.log"

echo "--- $(date) ---" >> "$LOG_FILE"
echo "Processing: $TORRENT_NAME (Category: $CATEGORY)" >> "$LOG_FILE"

# Use Python + guessit for smart parsing
python3 - <<EOF >> "$LOG_FILE" 2>&1
import os
import shutil
from guessit import guessit

content_path = "$CONTENT_PATH"
category = "$CATEGORY".strip().upper()
save_path = "$SAVE_PATH"

def sanitize(text):
    return text.replace('/', '-').replace(':', '-').strip()

def process():
    if not os.path.exists(content_path):
        print(f"Error: {content_path} not found")
        return

    # Guess metadata
    name = os.path.basename(content_path)
    guess = guessit(name)

    title = guess.get('title')
    year = guess.get('year')
    season = guess.get('season')
    episode = guess.get('episode')

    if not title:
        print(f"Could not guess title for {name}, skipping.")
        return

    title = sanitize(title)

    # TV SHOWS Logic
    if "TV" in category or season is not None:
        if season is None: season = 1
        season_str = f"Season {int(season):02d}"

        target_dir = os.path.join(save_path, title, season_str)
        os.makedirs(target_dir, exist_ok=True)

        if os.path.isfile(content_path):
            ext = os.path.splitext(content_path)[1]
            ep_str = f"S{int(season):02d}E{int(episode):02d}" if episode else "S" + str(season)
            new_filename = f"{title} - {ep_str}{ext}"
            target_path = os.path.join(target_dir, new_filename)

            print(f"Moving file to: {target_path}")
            shutil.move(content_path, target_path)

        elif os.path.isdir(content_path):
            print(f"Processing directory: {name}")
            for root, dirs, files in os.walk(content_path):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                        f_guess = guessit(f)
                        f_ep = f_guess.get('episode') or episode
                        f_s = f_guess.get('season') or season

                        ext = os.path.splitext(f)[1]
                        ep_str = f"S{int(f_s):02d}E{int(f_ep):02d}" if f_ep else "Extra"
                        new_f = f"{title} - {ep_str}{ext}"

                        src = os.path.join(root, f)
                        dst = os.path.join(target_dir, new_f)
                        print(f"Moving {f} -> {dst}")
                        shutil.move(src, dst)

            # Remove old dir if empty
            try: shutil.rmtree(content_path)
            except: pass

    # FILMS Logic
    else:
        folder_name = f"{title} ({year})" if year else title
        target_dir = os.path.join(save_path, folder_name)
        os.makedirs(target_dir, exist_ok=True)

        if os.path.isfile(content_path):
            ext = os.path.splitext(content_path)[1]
            new_filename = f"{folder_name}{ext}"
            target_path = os.path.join(target_dir, new_filename)
            shutil.move(content_path, target_path)

        elif os.path.isdir(content_path):
            for root, dirs, files in os.walk(content_path):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                        ext = os.path.splitext(f)[1]
                        shutil.move(os.path.join(root, f), os.path.join(target_dir, f"{folder_name}{ext}"))
            try: shutil.rmtree(content_path)
            except: pass

process()
EOF
