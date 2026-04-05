CREATE TABLE IF NOT EXISTS users (
    id            TEXT    PRIMARY KEY,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id            TEXT    PRIMARY KEY,
    user_id       TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    author        TEXT    NOT NULL,
    genre         TEXT,
    total_pages   INTEGER,
    current_page  INTEGER NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL
                          CHECK (status IN ('not_started', 'reading', 'completed')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_books_user_id ON books (user_id);
