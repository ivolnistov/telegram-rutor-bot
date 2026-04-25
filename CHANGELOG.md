# CHANGELOG

<!-- version list -->

## v1.2.0 (2026-04-25)

### Bug Fixes

- Add build context to root docker-compose for qbittorrent
  ([`32e8af6`](https://github.com/ivolnistov/telegram-rutor-bot/commit/32e8af64dd8e3953e7355339ec9fa96316fcfe1f))

- Bypass qBittorrent auth login if IP is whitelisted, update docker-compose build context, and add
  missing translations
  ([`f41e851`](https://github.com/ivolnistov/telegram-rutor-bot/commit/f41e851f9b178bd581882fcede797ac6bc9e2e63))

- Handle absolute poster URLs in Discovery page
  ([`6bfd64b`](https://github.com/ivolnistov/telegram-rutor-bot/commit/6bfd64b4280e7100769a2ca49016c713b6855f41))

- Make tests green and fix linting errors
  ([`3e13b92`](https://github.com/ivolnistov/telegram-rutor-bot/commit/3e13b923bc63f9c899094f521bdcedbfa082d002))

- Only notify about films with genuinely new torrents
  ([`4ef7101`](https://github.com/ivolnistov/telegram-rutor-bot/commit/4ef7101b30fbbc260d1795013a3bd1116abd0781))

- Remove unused RutorClient import and initialization
  ([`a120155`](https://github.com/ivolnistov/telegram-rutor-bot/commit/a120155112895902af030b20c5e3c0046e613371))

- Resolve test failures, lint and formatting issues
  ([`16d7dc4`](https://github.com/ivolnistov/telegram-rutor-bot/commit/16d7dc4861cf5c58d46bea69bc47f7bf04ffd7b2))

- Restore user-modified qbittorrent rename script and custom root build
  ([`bffb4d6`](https://github.com/ivolnistov/telegram-rutor-bot/commit/bffb4d65bb5250d81515762e261d86c4070c0722))

- **api**: Use TorrentResponse for list_torrents endpoint return type
  ([`2adcd4f`](https://github.com/ivolnistov/telegram-rutor-bot/commit/2adcd4fefaa4429742b0523ac11db0a856c7bfb3))

- **api**: Use TorrentResponse schema for get_media_torrents endpoint
  ([`f6bed7a`](https://github.com/ivolnistov/telegram-rutor-bot/commit/f6bed7abfb8b3cc90e0bdc4bdec9b4ab29c5afee))

- **ci**: Allowlist tmdb key in plex script from gitleaks
  ([`0922311`](https://github.com/ivolnistov/telegram-rutor-bot/commit/0922311f7263e32685e6d17154e094abbb8bb0fd))

- **ci**: Combine multiple workflows into a single pipeline and fix test failure
  ([`de66f45`](https://github.com/ivolnistov/telegram-rutor-bot/commit/de66f4558813d01488bd9727d92408977c136d6b))

- **ci**: Pin ruff<0.15, commit uv.lock, fix CI test failures
  ([`8a38ff6`](https://github.com/ivolnistov/telegram-rutor-bot/commit/8a38ff6afd0227df3441bfeb68ffaf4221e0138a))

- **ci**: Resolve pylint singleton comparisons and trufflehog config
  ([`72c49f3`](https://github.com/ivolnistov/telegram-rutor-bot/commit/72c49f3266d67b6cdef73ace2d239f5a65853a45))

- **db**: Add tmdb_session_id column to initial migration
  ([`4717316`](https://github.com/ivolnistov/telegram-rutor-bot/commit/4717316521edc7e2158a80c0fb90c5506c41c0aa))

- **db**: Parametrize films search and use postgres-compatible SQL
  ([`92ec7b9`](https://github.com/ivolnistov/telegram-rutor-bot/commit/92ec7b9bf15201fb86d090b661fa8a106c1d42e8))

- **docker**: Add frontend build stage to Dockerfile
  ([`8eab4a0`](https://github.com/ivolnistov/telegram-rutor-bot/commit/8eab4a07c5a00c989b3092c951e6a001494861cc))

- **frontend**: Handle undefined vote_average in Discovery
  ([`7d105b6`](https://github.com/ivolnistov/telegram-rutor-bot/commit/7d105b6b9bfb575e7cc239af8adc9200a33460fc))

- **lint**: Replace != None with is_not(None) for sqlalchemy
  ([`ae5d130`](https://github.com/ivolnistov/telegram-rutor-bot/commit/ae5d1309c5848ae1fbb701715584a530cb400287))

- **rutor**: Restore download link in formatted torrent message
  ([`2b99ffb`](https://github.com/ivolnistov/telegram-rutor-bot/commit/2b99ffb0cfdc06816c770df7246daa0fe01e2e5f))

- **security**: Resolve SonarCloud vulnerabilities
  ([`ade2e9f`](https://github.com/ivolnistov/telegram-rutor-bot/commit/ade2e9ff817fa916f7350554ad69e5f029811c2d))

- **tests**: Align stale tests with renamed/extended discovery API
  ([#5](https://github.com/ivolnistov/telegram-rutor-bot/pull/5),
  [`749f41b`](https://github.com/ivolnistov/telegram-rutor-bot/commit/749f41be63efa39b57ace02148744a65013eb126))

- **web**: Make frontend assets mount conditional
  ([`fc66c60`](https://github.com/ivolnistov/telegram-rutor-bot/commit/fc66c60606205014e2e0af52aad62d1ccb38c944))

### Chores

- Fix linter errors and code quality issues
  ([`d8e951d`](https://github.com/ivolnistov/telegram-rutor-bot/commit/d8e951d4ebf612019c1d76c2ba3414e1cb5ca2eb))

- Remove custom qbittorrent build and rename script
  ([`a1c39c7`](https://github.com/ivolnistov/telegram-rutor-bot/commit/a1c39c788de746a8cf2f94c3011eee824eab503f))

- Remove temporary deployment tarballs and ignore them
  ([`d199b9a`](https://github.com/ivolnistov/telegram-rutor-bot/commit/d199b9a44893613efaaa0c6aa735ac592f72471e))

- Setup formatters and linters for frontend and markdown
  ([`5e5d982`](https://github.com/ivolnistov/telegram-rutor-bot/commit/5e5d9829b72e6f2c0611143e8f6d82dfc47ab615))

- **lint**: Dedupe pylint and ruff so we only suppress once
  ([#5](https://github.com/ivolnistov/telegram-rutor-bot/pull/5),
  [`749f41b`](https://github.com/ivolnistov/telegram-rutor-bot/commit/749f41be63efa39b57ace02148744a65013eb126))

- **types**: Replace stray Any with Torrent/Tag in helpers + parser
  ([`5f954b4`](https://github.com/ivolnistov/telegram-rutor-bot/commit/5f954b40179f8000d5c4a714770dc60d059b170d))

### Continuous Integration

- Add trufflehog secret scanner workflow
  ([`c272ba8`](https://github.com/ivolnistov/telegram-rutor-bot/commit/c272ba8de27e71a18c7e47ed9e233395a6f1621e))

- Run docker build only on test branch or version tags
  ([`11b5e10`](https://github.com/ivolnistov/telegram-rutor-bot/commit/11b5e108dee3d9c756274eb93a1b2aea70e09fd3))

### Features

- Add KP rating, country flags, and UI enhancements
  ([`3fafaf2`](https://github.com/ivolnistov/telegram-rutor-bot/commit/3fafaf20dec119dcf7ae8f2cabd0d37edea04872))

- Add Searches page with Run Now button and notify toggle
  ([`fdd95dc`](https://github.com/ivolnistov/telegram-rutor-bot/commit/fdd95dc0bdd8b99999b302164c3ac1b31b1752ed))

- Add TV series episode parsing and is_series support
  ([`725a5f7`](https://github.com/ivolnistov/telegram-rutor-bot/commit/725a5f75c7ea70f1abaca5d2f668a765f2b5804f))

- Default plex rename script to false and require explicit ENABLE_PLEX_RENAME
  ([`baff226`](https://github.com/ivolnistov/telegram-rutor-bot/commit/baff226fcae5dea87737675cb3d1d8737c4f28ae))

- Handle series deduplication and category settings for searches
  ([`35d1ee5`](https://github.com/ivolnistov/telegram-rutor-bot/commit/35d1ee56443dc8f85484dc9e1b92e0bfee8bc6a5))

- Migrate system searches to database and support dynamic year variables
  ([`4484cbc`](https://github.com/ivolnistov/telegram-rutor-bot/commit/4484cbc0256d3f4c1a6b8568fb80d2577f3722c2))

- Per-search filters, search CRUD modal, fix tasks and category UI
  ([`7a3ab3e`](https://github.com/ivolnistov/telegram-rutor-bot/commit/7a3ab3ea7a3812d5f26f2894010ba493d2272139))

- Whitelist local subnets in qbittorrent webui to prevent docker ip bans
  ([`2c69c34`](https://github.com/ivolnistov/telegram-rutor-bot/commit/2c69c34a2839e72d4ccb00f4a7bcccebc35a0423))

- **discovery**: TMDB-driven film cards, /discovery command, configurable sort
  ([`d12fb31`](https://github.com/ivolnistov/telegram-rutor-bot/commit/d12fb31210fbe58e98e82b9e631b5558ef01fdab))

- **docker**: Add multi-platform build support (amd64, arm64)
  ([`ac83111`](https://github.com/ivolnistov/telegram-rutor-bot/commit/ac831116f5866f2afce663b40139d7d64f645a76))

### Refactoring

- Centralize notifications, deduplicate API actions, and increase test coverage to 80%
  ([`a3ac644`](https://github.com/ivolnistov/telegram-rutor-bot/commit/a3ac64408faeff2735799ec967f271991446a6ba))

- **parser**: Hoist TmdbMatcher import to module top
  ([#5](https://github.com/ivolnistov/telegram-rutor-bot/pull/5),
  [`749f41b`](https://github.com/ivolnistov/telegram-rutor-bot/commit/749f41be63efa39b57ace02148744a65013eb126))

### Testing

- **rutor**: Fix assertions for real torrent parsing
  ([`e07bcc3`](https://github.com/ivolnistov/telegram-rutor-bot/commit/e07bcc34f8b98851b1fbb133d13a823f58d0cbe0))


## v1.1.0 (2026-01-24)

### Bug Fixes

- **tests**: Update get_torrent_info signature in tests
  ([`0111d2d`](https://github.com/ivolnistov/telegram-rutor-bot/commit/0111d2de4ff04594dbbd2ced401999e9488899c9))

### Features

- Add pause and resume endpoints for downloads
  ([`5f60dc8`](https://github.com/ivolnistov/telegram-rutor-bot/commit/5f60dc893def08646bf3b434bc66fdb31e679c8e))

## v1.0.1 (2026-01-18)

### Bug Fixes

- **tests**: Remove transmission tests
  ([`924f1d4`](https://github.com/ivolnistov/telegram-rutor-bot/commit/924f1d42e5fdffa4d0337c8546d29f7ba9cba5bb))

## v1.0.0 (2026-01-18)

- Initial Release
