CREATE TABLE IF NOT EXISTS films(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    blake         TEXT    NOT NULL,
    year          INTEGER NOT NULL,
    name          TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS torrents(
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    film_id       TEXT    NOT NULL,
    blake TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    magnet        TEXT    NOT NULL UNIQUE,
    created       DATE    NOT NULL,
    link          TEXT    NOT NULL,
    sz            INTEGER NOT NULL,
    approved      INTEGER DEFAULT FALSE,
    downloaded    INTEGER DEFAULT FALSE,
    FOREIGN KEY(film_id) REFERENCES films(id)
);
CREATE TABLE IF NOT EXISTS user(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id  INTEGER NOT NULL

);
CREATE TABLE IF NOT EXISTS searches
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    url          TEXT    NOT NULL,
    cron         TEXT    NOT NULL,
    last_success DATE,
    creator_id   INTEGER,
    FOREIGN KEY(creator_id) REFERENCES user(id)
);
CREATE TABLE IF NOT EXISTS subscribes (
    search_id INTEGER,
    user_id INTEGER,
    UNIQUE(search_id, user_id),
    FOREIGN KEY(search_id) REFERENCES searches(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);