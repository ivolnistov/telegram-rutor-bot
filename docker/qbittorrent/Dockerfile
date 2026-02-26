FROM lscr.io/linuxserver/qbittorrent:5.0.3

# Install python, pip, and mkvtoolnix
RUN apk add --no-cache python3 py3-pip mkvtoolnix && \
    pip install --break-system-packages guessit requests

# Copy the rename script to a temporary location (will be moved by init script)
COPY plex_rename.sh /app/plex_rename.sh

# Copy the setup script to the custom initialization directory
COPY setup.sh /custom-cont-init.d/90-setup-qbittorrent.sh

# Ensure executable permissions
RUN chmod +x /app/plex_rename.sh && \
    chmod +x /custom-cont-init.d/90-setup-qbittorrent.sh
