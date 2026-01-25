# API Documentation

## Bot Commands

### User Commands

#### `/start`

Initialize bot interaction and verify user authorization.

**Usage**: `/start`

**Response**: Welcome message if authorized, unauthorized message otherwise.

#### `/search <query>`

Search for torrents on rutor.info.

**Usage**: `/search The Matrix 2021`

**Response**: List of found torrents with inline commands.

#### `/list`

Show the 20 most recent torrents in the database.

**Usage**: `/list`

**Response**: Formatted list of torrents with metadata.

#### `/add <url>`

Add a new search subscription.

**Usage**: `/add http://rutor.info/search/0/0/100/0/matrix`

**Response**: Confirmation with search ID.

#### `/all`

Display all your search subscriptions.

**Usage**: `/all`

**Response**: List of all searches with their schedules.

#### `/del <id>`

Delete a search subscription.

**Usage**: `/del 5`

**Response**: Confirmation of deletion.

#### `/now <id>`

Execute a search immediately.

**Usage**: `/now 5`

**Response**: Search results or "no new torrents" message.

#### `/subscriptions`

List all your active subscriptions.

**Usage**: `/subscriptions`

**Response**: List of subscribed searches.

### Inline Commands

These commands are generated dynamically based on torrent/search IDs:

#### `/dl_<id>`

Download a torrent to the configured client.

**Usage**: `/dl_12345`

**Response**: Confirmation message with torrent name.

#### `/in_<id>`

Get detailed information about a torrent including poster and screenshots.

**Usage**: `/in_12345`

**Response**:

- Torrent details (description, quality, etc.)
- Poster image (if available)
- Screenshots (up to 3)

#### `/subscribe_<id>`

Subscribe to notifications for a search.

**Usage**: `/subscribe_5`

**Response**: Subscription confirmation.

#### `/unsubscribe_<id>`

Unsubscribe from search notifications.

**Usage**: `/unsubscribe_5`

**Response**: Unsubscription confirmation.

## Database API

### User Operations

```python
from telegram_rutor_bot.db import get_async_session, get_or_create_user_by_chat_id

async with get_async_session() as session:
    user = await get_or_create_user_by_chat_id(
        session,
        chat_id=123456789,
        username="john_doe",
        first_name="John",
        last_name="Doe"
    )
```

### Search Operations

```python
from telegram_rutor_bot.db import add_search_to_db, get_searches

# Add search
async with get_async_session() as session:
    search = await add_search_to_db(
        session,
        user_id=user.id,
        url="http://rutor.info/search/...",
        query="matrix"
    )

# Get all searches
async with get_async_session() as session:
    searches = await get_searches(session, show_empty=False)
```

### Torrent Operations

```python
from telegram_rutor_bot.db import add_torrent, get_torrent_by_id

# Add torrent
async with get_async_session() as session:
    torrent = await add_torrent(
        session,
        film_id=film.id,
        blake="hash",
        name="Movie.2021.1080p",
        magnet="magnet:?xt=...",
        link="/torrent/123456",
        size=1234567890
    )

# Get torrent
async with get_async_session() as session:
    torrent = await get_torrent_by_id(session, torrent_id)
```

## Torrent Client API

### Client Interface

All torrent clients implement the same interface:

```python
from telegram_rutor_bot.torrent_clients import get_torrent_client

client = get_torrent_client()
await client.connect()

# Add torrent
result = await client.add_torrent(magnet_link)

# Get torrent info
info = await client.get_torrent(torrent_id)

# List all torrents
torrents = await client.list_torrents()

# Control torrents
await client.pause_torrent(torrent_id)
await client.resume_torrent(torrent_id)
await client.remove_torrent(torrent_id, delete_files=True)

await client.disconnect()
```

### Response Format

#### Add Torrent Response

```json
{
    "id": "torrent_id",
    "name": "Torrent Name",
    "hash": "torrent_hash"
}
```

#### Torrent Info Response

```json
{
    "id": "torrent_id",
    "name": "Torrent Name",
    "hash": "torrent_hash",
    "size": 1234567890,
    "progress": 45.5,
    "status": "downloading",
    "download_rate": 1048576,
    "upload_rate": 524288,
    "download_dir": "/downloads"
}
```

## Parser API

### Parse Rutor Page

```python
from telegram_rutor_bot.rutor import parse_rutor
from telegram_rutor_bot.db import get_async_session

async with get_async_session() as session:
    new_film_ids = await parse_rutor(url, session)
```

### Get Torrent Information

```python
from telegram_rutor_bot.rutor import get_torrent_info

message, poster, images = await get_torrent_info(
    torrent_link="/torrent/123456",
    download_command="/dl_123"
)
```

## TaskIQ Tasks

### Notify About New Torrents

```python
from telegram_rutor_bot.tasks.jobs import notify_about_new

# Schedule notification
await notify_about_new.kiq(search_id)
```

### Check Scheduled Searches

```python
from telegram_rutor_bot.tasks.jobs import check_scheduled_searches

# Run scheduled check
await check_scheduled_searches.kiq()
```

## Models

### User Model

```python
class User(Base):
    id: int
    chat_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    blocked: bool = False
    created: datetime
    last_update: datetime
```

### Film Model

```python
class Film(Base):
    id: int
    blake: str  # Hash of film name
    year: int
    name: str
    torrents: list[Torrent]
```

### Torrent Model

```python
class Torrent(Base):
    id: int
    film_id: int
    blake: str  # Hash of torrent link
    name: str
    magnet: str
    link: str
    size: int
    approved: bool
    downloaded: bool
    created: datetime
    date: datetime
    seeds: int
```

### Search Model

```python
class Search(Base):
    id: int
    user_id: int
    url: str
    query: str
    empty: bool
    last_success: datetime | None
    # Cron schedule fields
    minute: str = '*'
    hour: str = '*'
    day: str = '*'
    month: str = '*'
    day_of_week: str = '*'
```

## Error Handling

The API uses standard Python exceptions:

- `ValueError` - Invalid input parameters
- `TorrentClientError` - Torrent client communication errors
- `httpx.HTTPError` - Network/HTTP errors
- `sqlalchemy.exc.IntegrityError` - Database constraint violations

Example error handling:

```python
from telegram_rutor_bot.torrent_clients import TorrentClientError

try:
    await client.add_torrent(magnet)
except TorrentClientError as e:
    logger.error(f"Failed to add torrent: {e}")
    await update.message.reply_text("Failed to add torrent")
```
