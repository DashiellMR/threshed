CREATE TABLE IF NOT EXISTS users (
    discord_account TEXT NOT NULL,
    username TEXT NOT NULL,
    tag TEXT NOT NULL,
    puuid TEXT NOT NULL,
    PRIMARY KEY (puuid)
);