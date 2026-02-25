#!/bin/bash

# Move rename script to a safe location
cp /app/plex_rename.sh /usr/local/bin/plex_rename.sh
chmod +x /usr/local/bin/plex_rename.sh

# Configure qBittorrent.conf
export CONFIG_FILE="/config/qBittorrent/qBittorrent.conf"

echo "Configuring qBittorrent AutoRun in $CONFIG_FILE..."

# Use heredoc for python script to avoid quoting hell
python3 - <<'EOF'
import configparser
import sys
import os
import base64
import hashlib

config_path = os.environ.get('CONFIG_FILE', '/config/qBittorrent/qBittorrent.conf')
script_path = '/usr/local/bin/plex_rename.sh'
cmd = f'/bin/bash {script_path} "%F" "%R" "%D" "%N" "%L"'

if not os.path.exists(config_path):
    print(f'Config file not found at {config_path}, skipping...')
    sys.exit(0)

enable_rename = os.environ.get('ENABLE_PLEX_RENAME', 'false').lower() == 'true'

if not enable_rename:
    print('ENABLE_PLEX_RENAME is not set to true, skipping AutoRun configuration.')
    # We still want to process BitTorrent and WebUI settings, so we just clear cmd
# Read config lines
lines = []
with open(config_path, 'r') as f:
    lines = f.readlines()

# --------------------------
# 1. Update [AutoRun]
# --------------------------
new_lines = []
in_autorun = False
autorun_found = False
program_set = False
enabled_set = False

enable_rename = os.environ.get('ENABLE_PLEX_RENAME', 'false').lower() == 'true'
enabled_val = "true" if enable_rename else "false"
cmd = f'/bin/bash {script_path} "%F" "%R" "%D" "%N" "%L"' if enable_rename else ""

if not enable_rename:
    print('ENABLE_PLEX_RENAME is not set to true, disabling AutoRun configuration.')

for line in lines:
    stripped = line.strip()
    if stripped == '[AutoRun]':
        in_autorun = True
        autorun_found = True
        new_lines.append(line)
        continue

    if stripped.startswith('[') and stripped.endswith(']'):
        if in_autorun:
            if not enabled_set:
                new_lines.append(f'enabled={enabled_val}\n')
            if not program_set:
                new_lines.append(f'program={cmd}\n')
        in_autorun = False
        new_lines.append(line)
        continue

    if in_autorun:
        if stripped.startswith('enabled='):
            new_lines.append(f'enabled={enabled_val}\n')
            enabled_set = True
        elif stripped.startswith('program='):
            new_lines.append(f'program={cmd}\n')
            program_set = True
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

if not autorun_found:
    new_lines.append('\n[AutoRun]\n')
    new_lines.append(f'enabled={enabled_val}\n')
    new_lines.append(f'program={cmd}\n')
elif in_autorun:
     if not enabled_set:
        new_lines.append(f'enabled={enabled_val}\n')
     if not program_set:
        new_lines.append(f'program={cmd}\n')

# --------------------------
# 2. Update [Preferences] & [BitTorrent]
# --------------------------

# Prepare password hash
conf_str = None
webui_password = os.environ.get('WEBUI_PASSWORD')
if webui_password:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha512', webui_password.encode(), salt, 100000)
    salt_b64 = base64.b64encode(salt).decode()
    hash_b64 = base64.b64encode(dk).decode()
    conf_str = f'@ByteArray({salt_b64}:{hash_b64})'

# Prepare Share Ratio logic
delete_after_ratio = os.environ.get('DELETE_AFTER_RATIO')
share_ratio_val = None
seeding_time_val = None
share_action_val = None

if delete_after_ratio is not None:
    try:
        ratio = float(delete_after_ratio)
        share_ratio_val = f'{ratio}'
        share_action_val = 'Remove' # Always remove if this env var is set
        if ratio == 0:
            seeding_time_val = '0' # Immediate removal
    except ValueError:
        print(f"Invalid DELETE_AFTER_RATIO value: {delete_after_ratio}, ignoring.")

final_lines = []
in_pref = False
in_bt = False

# Flags for Preferences
password_set = False
host_header_set = False
csrf_set = False

# Flags for BitTorrent
ratio_set = False
time_set = False
action_set = False

for line in new_lines:
    stripped = line.strip()

    # Check section headers
    if stripped == '[Preferences]':
        in_pref = True
        in_bt = False
        final_lines.append(line)
        continue
    elif stripped == '[BitTorrent]':
        in_bt = True
        in_pref = False
        final_lines.append(line)
        continue

    if stripped.startswith('[') and stripped.endswith(']'):
        # Leaving a section
        if in_pref:
             if conf_str and not password_set: final_lines.append(f'WebUI\\Password_PBKDF2={conf_str}\n')
             if not host_header_set: final_lines.append('WebUI\\HostHeaderValidation=false\n')
             if not csrf_set: final_lines.append('WebUI\\CSRFProtection=false\n')
        elif in_bt:
             if share_ratio_val and not ratio_set: final_lines.append(f'Session\\ShareRatioLimit={share_ratio_val}\n')
             if seeding_time_val and not time_set: final_lines.append(f'Session\\SeedingTimeLimit={seeding_time_val}\n')
             if share_action_val and not action_set: final_lines.append(f'Session\\ShareLimitAction={share_action_val}\n')

        in_pref = False
        in_bt = False
        final_lines.append(line)
        continue

    if in_pref:
        if stripped.startswith('WebUI\\Password_PBKDF2='):
            if conf_str:
                final_lines.append(f'WebUI\\Password_PBKDF2={conf_str}\n')
                password_set = True
            else:
                final_lines.append(line)
        elif stripped.startswith('WebUI\\HostHeaderValidation='):
            final_lines.append('WebUI\\HostHeaderValidation=false\n')
            host_header_set = True
        elif stripped.startswith('WebUI\\CSRFProtection='):
            final_lines.append('WebUI\\CSRFProtection=false\n')
            csrf_set = True
        else:
            final_lines.append(line)

    elif in_bt:
        if stripped.startswith('Session\\ShareRatioLimit='):
            if share_ratio_val:
                final_lines.append(f'Session\\ShareRatioLimit={share_ratio_val}\n')
                ratio_set = True
            else:
                final_lines.append(line)
        elif stripped.startswith('Session\\SeedingTimeLimit='):
            if seeding_time_val:
                final_lines.append(f'Session\\SeedingTimeLimit={seeding_time_val}\n')
                time_set = True
            else:
                final_lines.append(line)
        elif stripped.startswith('Session\\ShareLimitAction='):
            if share_action_val:
                final_lines.append(f'Session\\ShareLimitAction={share_action_val}\n')
                action_set = True
            else:
                final_lines.append(line)
        else:
            final_lines.append(line)

    else:
        final_lines.append(line)

# Handle end of file
if in_pref:
     if conf_str and not password_set: final_lines.append(f'WebUI\\Password_PBKDF2={conf_str}\n')
     if not host_header_set: final_lines.append('WebUI\\HostHeaderValidation=false\n')
     if not csrf_set: final_lines.append('WebUI\\CSRFProtection=false\n')
elif in_bt:
     if share_ratio_val and not ratio_set: final_lines.append(f'Session\\ShareRatioLimit={share_ratio_val}\n')
     if seeding_time_val and not time_set: final_lines.append(f'Session\\SeedingTimeLimit={seeding_time_val}\n')
     if share_action_val and not action_set: final_lines.append(f'Session\\ShareLimitAction={share_action_val}\n')

with open(config_path, 'w') as f:
    f.writelines(final_lines)

print("Configuration (AutoRun + Preferences + BitTorrent) updated.")
EOF
