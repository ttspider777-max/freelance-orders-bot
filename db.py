import sqlite3

conn = sqlite3.connect("seen.db")
conn.execute("CREATE TABLE IF NOT EXISTS seen (key TEXT PRIMARY KEY)")
conn.execute(
    "CREATE TABLE IF NOT EXISTS orders (key TEXT PRIMARY KEY, title TEXT, description TEXT, url TEXT, budget TEXT, source TEXT)"
)
conn.commit()

FIELDS = ("key", "title", "description", "url", "budget", "source")


def is_seen(key: str) -> bool:
    return conn.execute("SELECT 1 FROM seen WHERE key=?", (key,)).fetchone() is not None


def mark_seen(key: str) -> None:
    conn.execute("INSERT OR IGNORE INTO seen VALUES (?)", (key,))
    conn.commit()


def save_order(o: dict) -> None:
    conn.execute("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", tuple(o[f] for f in FIELDS))
    conn.commit()


def get_order(key: str) -> dict | None:
    r = conn.execute(f"SELECT {','.join(FIELDS)} FROM orders WHERE key=?", (key,)).fetchone()
    return dict(zip(FIELDS, r)) if r else None
