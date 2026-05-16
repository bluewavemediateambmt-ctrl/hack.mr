import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# SAFE TABLE CREATE (fixes your "no such column id" issue)
cur.execute("DROP TABLE IF EXISTS users")

cur.execute("""
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT,
    points INTEGER DEFAULT 3,
    ban INTEGER DEFAULT 0,
    ref TEXT
)
""")

conn.commit()


def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    return cur.fetchone()


def create_user(uid, name, ref=None):
    if not get_user(uid):

        # referral bonus
        if ref:
            cur.execute("SELECT id FROM users WHERE id=?", (ref,))
            if cur.fetchone():
                cur.execute("UPDATE users SET points = points + 10 WHERE id=?", (ref,))

        cur.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)",
                    (uid, name, 3, 0, ref))
        conn.commit()


def update_points(uid, value):
    cur.execute("UPDATE users SET points=? WHERE id=?", (value, uid))
    conn.commit()


def add_points(uid, value):
    cur.execute("UPDATE users SET points = points + ? WHERE id=?", (value, uid))
    conn.commit()


def ban_user(uid):
    cur.execute("UPDATE users SET ban=1 WHERE id=?", (uid,))
    conn.commit()


def unban_user(uid):
    cur.execute("UPDATE users SET ban=0 WHERE id=?", (uid,))
    conn.commit()


def is_banned(uid):
    cur.execute("SELECT ban FROM users WHERE id=?", (uid,))
    r = cur.fetchone()
    return r and r[0] == 1


def top_users():
    cur.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 5")
    return cur.fetchall()


def all_users():
    cur.execute("SELECT id FROM users")
    return cur.fetchall()


def stats():
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT SUM(points) FROM users")
    points = cur.fetchone()[0] or 0

    return users, points
