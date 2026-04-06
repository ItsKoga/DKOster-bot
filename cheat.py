import sqlite3
import time


USER_ID = "499198101383282689"
DB_PATH = "data.db"


def normalize_egg_type(egg_type: str) -> str:
    mapping = {
        "Schokoei": "Schokoei",
        "gekochtes Hühnerei": "cooked",
        "ungekochtes Hühnerei": "uncooked",
        "cooked": "cooked",
        "uncooked": "uncooked",
    }
    return mapping.get(egg_type, egg_type)


def ensure_user(cur: sqlite3.Cursor, user_id: str) -> None:
    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))


def add_egg(cur: sqlite3.Cursor, user_id: str, egg_type: str) -> None:
    egg_type = normalize_egg_type(egg_type)

    if egg_type == "Schokoei":
        cur.execute(
            "UPDATE users SET chocolate_eggs = COALESCE(chocolate_eggs, 0) + 1 WHERE user_id = ?",
            (user_id,),
        )
        return

    if egg_type not in {"cooked", "uncooked"}:
        raise ValueError(f"Unknown egg type: {egg_type}")

    cur.execute(
        "INSERT INTO eggs (owner_id, creator_id, type, rotten_ts) VALUES (?, ?, ?, ?)",
        (user_id, user_id, egg_type, int(time.time())),
    )


def refresh_points(cur: sqlite3.Cursor, user_id: str) -> int:
    row = cur.execute(
        "SELECT COALESCE(chocolate_eggs, 0), COALESCE(cakes, 0) FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    chocolate_eggs, cakes = int(row[0]), int(row[1])
    points = chocolate_eggs + cakes * 10
    cur.execute("UPDATE users SET points = ? WHERE user_id = ?", (points, user_id))
    return points


def main() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        ensure_user(cur, USER_ID)

        for i in range(1000):
            print(i)
            add_egg(cur, USER_ID, "Schokoei")

        for i in range(10):
            print(i)
            add_egg(cur, USER_ID, "gekochtes Hühnerei")

        for i in range(10):
            print(i)
            add_egg(cur, USER_ID, "ungekochtes Hühnerei")

        points = refresh_points(cur, USER_ID)
        conn.commit()
        print(f"Updated points: {points}")


if __name__ == "__main__":
    main()