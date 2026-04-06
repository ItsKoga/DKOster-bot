import sqlite3
import time

import random


SYSTEM_USER_ID = "111111111111111111"
TOP_N = 5


def table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    row = cursor.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def stat_value(stats: dict[str, int], key: str) -> int:
    return int(stats.get(key, 0))


def print_top(title: str, entries: list[tuple[str, float]], suffix: str = ""):
    print(title)
    if not entries:
        print("Keine Daten vorhanden.")
        return

    for i, (user_id, value) in enumerate(entries[:TOP_N], start=1):
        if isinstance(value, float):
            print(f"{i}. <@{user_id}> : {value:.2f}{suffix}")
        else:
            print(f"{i}. <@{user_id}> : {int(value)}{suffix}")


def main():
    start = time.time()

    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    users = cur.execute(
        """
        SELECT user_id, egg_talisman, rabbit_foot_count, used_rabbit_foot_count,
             points, cakes, chocolate_eggs, used_collect, found_nests, tickets,
               eggs_throwen, eggs_hit, own_eggs_hit, eggs_throwen_at
        FROM users
        WHERE user_id != ?
        """,
        (SYSTEM_USER_ID,),
    ).fetchall()

    stats_rows = cur.execute("SELECT stat, value FROM stats").fetchall() if table_exists(cur, "stats") else []
    stats = {row["stat"]: int(row["value"]) for row in stats_rows}

    print(f"Users Gesamt: {len(users)}")
    total_points = sum(int(user["points"]) for user in users)
    print(f"Punkte insgesamt: {total_points}")

    users_with_talisman = [user for user in users if int(user["egg_talisman"]) != 0]
    print(f"User mit Talisman: {len(users_with_talisman)}")

    current_rabbit_foots = sum(int(user["rabbit_foot_count"]) for user in users)
    used_rabbit_foots = sum(int(user["used_rabbit_foot_count"]) for user in users)
    print(f"Aktuelle Hasenpfoten: {current_rabbit_foots}")
    print(f"Benutzte Hasenpfoten: {used_rabbit_foots}")
    print(f"Hasenpfoten insgesamt: {current_rabbit_foots + used_rabbit_foots}")

    total_collects = sum(int(user["used_collect"]) for user in users)
    print(f"/collect ausgeführt: {total_collects}")

    total_found_nests = sum(int(user["found_nests"]) for user in users)
    print(f"Nester gefunden(nicht leer): {total_found_nests}")

    total_tickets = sum(int(user["tickets"]) for user in users)
    print(f"Tickets insgesamt: {total_tickets}")

    print("\n")

    collect_ranking = sorted(
        [(str(user["user_id"]), int(user["used_collect"])) for user in users],
        key=lambda x: x[1],
        reverse=True,
    )
    print_top("Top 5 User, die am meisten /collect ausgeführt haben:", collect_ranking)

    cakes_ranking = sorted(
        [(str(user["user_id"]), int(user["cakes"])) for user in users],
        key=lambda x: x[1],
        reverse=True,
    )
    print_top("**Top 5 User, die die meisten Kuchen erstellt haben:**", cakes_ranking, " Kuchen")

    tickets_ranking = sorted(
        [(str(user["user_id"]), int(user["tickets"])) for user in users],
        key=lambda x: x[1],
        reverse=True,
    )
    print_top("Top 5 User mit den meisten Tickets:", tickets_ranking, " Tickets")

    print("\n")

    eggs = cur.execute("SELECT owner_id, creator_id, type FROM eggs").fetchall() if table_exists(cur, "eggs") else []
    print(f"Kuchen insgesamt: {sum(int(user['cakes']) for user in users)}")

    # Im neuen Schema liegen Schokoeier im users.chocolate_eggs Feld.
    total_chocolate_eggs = sum(int(user["chocolate_eggs"]) for user in users)
    print(f"Schokoeier insgesamt gefunden: {total_chocolate_eggs}")

    total_cooked_found = len([egg for egg in eggs if egg["type"] == "cooked"]) + stat_value(stats, "deleted_cooked")
    total_uncooked_found = len([egg for egg in eggs if egg["type"] == "uncooked"]) + stat_value(stats, "deleted_uncooked")
    print(f"Gekochte Eier insgesamt gefunden: {total_cooked_found}")
    print(f"Ungekochte Eier insgesamt gefunden: {total_uncooked_found}")

    print("\n")

    solo_fights = (
        cur.execute("SELECT challenger_id, defender_id, winner_id FROM egg_fights").fetchall()
        if table_exists(cur, "egg_fights")
        else []
    )
    print(f"Kämpfe insgesamt: {len(solo_fights)}")

    print("\n")

    fight_stats: dict[str, dict[str, int]] = {
        str(user["user_id"]): {"fights": 0, "wins": 0, "losses": 0, "started": 0, "accepted": 0}
        for user in users
    }

    for fight in solo_fights:
        challenger = str(fight["challenger_id"])
        defender = str(fight["defender_id"])
        winner = str(fight["winner_id"])

        if challenger in fight_stats:
            fight_stats[challenger]["fights"] += 1
            fight_stats[challenger]["started"] += 1
        if defender in fight_stats:
            fight_stats[defender]["fights"] += 1
            fight_stats[defender]["accepted"] += 1
        if winner in fight_stats:
            fight_stats[winner]["wins"] += 1

    for uid, values in fight_stats.items():
        values["losses"] = values["fights"] - values["wins"]

    print_top(
        "**Top 5 User, die die meisten Solo-Fights gewonnen haben:**",
        sorted([(uid, v["wins"]) for uid, v in fight_stats.items()], key=lambda x: x[1], reverse=True),
        " Siege",
    )
    print_top(
        "**Top 5 User, die die meisten Solo-Fights verloren haben:**",
        sorted([(uid, v["losses"]) for uid, v in fight_stats.items()], key=lambda x: x[1], reverse=True),
        " Niederlagen",
    )
    print_top(
        "**Top 5 User, die die meisten Solo-Fights gestartet haben:**",
        sorted([(uid, v["started"]) for uid, v in fight_stats.items()], key=lambda x: x[1], reverse=True),
        " Kämpfe gestartet",
    )
    print_top(
        "**Top 5 User, die die meisten Solo-Fight Anfragen angenommen haben:**",
        sorted([(uid, v["accepted"]) for uid, v in fight_stats.items()], key=lambda x: x[1], reverse=True),
        " Anfragen angenommen",
    )

    winrate_ranking: list[tuple[str, float]] = []
    for uid, values in fight_stats.items():
        if values["fights"] >= 30:
            winrate = (values["wins"] / values["fights"]) * 100
            winrate_ranking.append((uid, winrate))
    winrate_ranking.sort(key=lambda x: x[1], reverse=True)
    print_top("**Top 5 User, die die höchste Gewinnrate haben(mindestens 30 Fights):**", winrate_ranking, "%")

    print("\n")

    
    throws_amount = 0
    for user in users:
        throws_amount += int(user["eggs_throwen"])

    print(f"Würfe insgesamt: {throws_amount}")
    print("\n")
    throw_stats = {
        str(user["user_id"]): {
            "throws": int(user["eggs_throwen"]),
            "successful": int(user["eggs_hit"]),
            "hits": int(user["own_eggs_hit"]),
            "hits_received": int(user["eggs_throwen_at"]),
        }
        for user in users
    }

    print_top(
        "**Top 5 User, die die meisten Eier geworfen haben:**",
        sorted([(uid, v["throws"]) for uid, v in throw_stats.items()], key=lambda x: x[1], reverse=True),
        " Würfe",
    )
    print_top(
        "**Top 5 User, die die meisten erfolgreichen Eierwürfe hatten:**",
        sorted([(uid, v["successful"]) for uid, v in throw_stats.items()], key=lambda x: x[1], reverse=True),
        " erfolgreiche Würfe",
    )
    print_top(
        "**Top 5 User, die am meisten abgeworfen wurden:**",
        sorted([(uid, v["hits_received"]) for uid, v in throw_stats.items()], key=lambda x: x[1], reverse=True),
        " Versuche",
    )
    print_top(
        "**Top 5 User, die am meisten von Eiern getroffen worden:**",
        sorted([(uid, v["hits"]) for uid, v in throw_stats.items()], key=lambda x: x[1], reverse=True),
        "x getroffen worden",
    )

    throwrate_ranking: list[tuple[str, float]] = []
    for uid, values in throw_stats.items():
        if values["throws"] >= 30:
            hitrate = (values["successful"] / values["throws"]) * 100
            throwrate_ranking.append((uid, hitrate))
    throwrate_ranking.sort(key=lambda x: x[1], reverse=True)
    print_top("**Top 5 User, die die höchste Trefferquote haben(mindestens 30 Würfe):**", throwrate_ranking, "%")

    print("\n")

    for location in ["1", "2", "3", "4", "5"]:
        print(f"An der Location {location} wurde {stat_value(stats, location)} mal gesucht")


    #giveaway
    users_giveaway = [(user[0], user[12]) for user in users]
    users_giveaway_ready = []
    for user in users_giveaway:
        for _ in range(user[1]):
            users_giveaway_ready.append(user[0])
    print(len(users_giveaway))

    for i in range(3):
        print(random.choice(users_giveaway_ready))

    conn.close()
    print(f"\nTime: {time.strftime('%M:%S', time.gmtime(time.time() - start))}")


if __name__ == "__main__":
    main()