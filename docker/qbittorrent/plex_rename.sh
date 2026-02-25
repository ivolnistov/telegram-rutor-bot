#!/bin/bash
# Ultra Smart Rename Script for Plex with TMDB & Tags Support
# $1: Content path, $2: Root path, $3: Save path, $4: Torrent name, $5: Category, $6: Tags

CONTENT_PATH="$1"
SAVE_PATH="$3"
TORRENT_NAME="$4"
CATEGORY="$5"
TAGS="$6"

LOG_FILE="/config/plex_rename.log"
TMDB_KEY="af702c5536acdf6b135a2284739b7c01"

echo "--- $(date) ---" >> "$LOG_FILE"
echo "Processing: $TORRENT_NAME" >> "$LOG_FILE"
echo "Tags: $TAGS" >> "$LOG_FILE"

# Use Python + guessit + TMDB + Tags for smart parsing
python3 - <<EOF >> "$LOG_FILE" 2>&1
import os
import shutil
import requests
import re
from guessit import guessit

content_path = "$CONTENT_PATH"
category = "$CATEGORY".strip().upper()
save_path = "$SAVE_PATH"
tmdb_key = "$TMDB_KEY"
tags = "$TAGS"

def sanitize(text):
    return text.replace('/', '-').replace(':', '-').strip()

def get_tmdb_id_from_tags(tags_str):
    # Look for tags like "tmdb:12345" or just "12345" if it's pure ID
    match = re.search(r'tmdb:(\d+)', tags_str, re.I)
    if match: return match.group(1)
    return None

def get_tmdb_id_from_api(title, year=None, is_show=False):
    if not tmdb_key: return None
    url = f"https://api.themoviedb.org/3/search/{'tv' if is_show else 'movie'}"
    params = {"api_key": tmdb_key, "query": title}
    if year: params["year" if not is_show else "first_air_date_year"] = year
    
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if data.get('results'):
            return data['results'][0].get('id')
    except Exception as e:
        print(f"TMDB Error: {e}")
    return None

def set_mkv_title(file_path, title):
    if not file_path.lower().endswith('.mkv'): return
    try:
        os.system(f'mkvpropedit "{file_path}" --set "title={title}"')
    except: pass

def write_id_file(folder_path, tmdb_id):
    if not tmdb_id: return
    try:
        with open(os.path.join(folder_path, "tmdb.id"), "w") as f:
            f.write(str(tmdb_id))
    except: pass

def process():
    if not os.path.exists(content_path):
        print(f"Error: {content_path} not found")
        return

    name = os.path.basename(content_path)
    guess = guessit(name)
    title = guess.get('title')
    if not title:
        guess = guessit("$TORRENT_NAME")
        title = guess.get('title')
    
    if not title:
        print(f"Could not guess title for {name}, skipping.")
        return

    year = guess.get('year')
    season = guess.get('season')
    episode = guess.get('episode')
    is_show = "TV" in category or season is not None
    
    # 1. Try to get ID from Tags
    tmdb_id = get_tmdb_id_from_tags(tags)
    
    # 2. Fallback to API search
    if not tmdb_id:
        print("No TMDB ID in tags, searching API...")
        tmdb_id = get_tmdb_id_from_api(title, year, is_show)
    
    tmdb_tag = f" {{tmdb-{tmdb_id}}}" if tmdb_id else ""
    
    clean_title = sanitize(title)
    display_title = f"{clean_title} ({year})" if year else clean_title
    
    if is_show:
        if season is None: season = 1
        season_str = f"Season {int(season):02d}"
        show_folder_name = f"{display_title}{tmdb_tag}"
        show_root = os.path.join(save_path, show_folder_name)
        target_dir = os.path.join(show_root, season_str)
        os.makedirs(target_dir, exist_ok=True)
        write_id_file(show_root, tmdb_id)
        
        files_to_process = []
        if os.path.isfile(content_path): files_to_process.append(content_path)
        else:
            for root, dirs, files in os.walk(content_path):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                        files_to_process.append(os.path.join(root, f))
        
        for f_path in files_to_process:
            f_guess = guessit(os.path.basename(f_path))
            f_ep = f_guess.get('episode') or episode
            f_s = f_guess.get('season') or season
            ext = os.path.splitext(f_path)[1]
            ep_str = f"S{int(f_s or season or 1):02d}E{int(f_ep):02d}" if f_ep else "Extra"
            new_f = f"{clean_title} - {ep_str}{ext}"
            dst = os.path.join(target_dir, new_f)
            shutil.move(f_path, dst)
            set_mkv_title(dst, f"{clean_title} - {ep_str}")
    else:
        folder_name = f"{display_title}{tmdb_tag}"
        target_dir = os.path.join(save_path, folder_name)
        os.makedirs(target_dir, exist_ok=True)
        write_id_file(target_dir, tmdb_id)
        
        if os.path.isfile(content_path):
            ext = os.path.splitext(content_path)[1]
            dst = os.path.join(target_dir, f"{folder_name}{ext}")
            shutil.move(content_path, dst)
            set_mkv_title(dst, display_title)
        elif os.path.isdir(content_path):
            for root, dirs, files in os.walk(content_path):
                for f in files:
                    if f.lower().endswith(('.mkv', '.mp4', '.avi')):
                        ext = os.path.splitext(f)[1]
                        dst = os.path.join(target_dir, f"{folder_name}{ext}")
                        shutil.move(os.path.join(root, f), dst)
                        set_mkv_title(dst, display_title)

    if os.path.isdir(content_path) and not os.listdir(content_path):
        os.rmdir(content_path)

process()
EOF
