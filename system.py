from __future__ import annotations

import asyncio
import random
import time as tm
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import aiosqlite
import discord
from discord.ext import tasks

import log_helper


# ----------------------------
# Helpers (wie früher)
# ----------------------------
def format_number(n, type="p"):
    # "p" steht für positive Zahlen
    if type == "p":
        return f"{abs(n):,}".replace(",", "_").replace(".", ",").replace("_", ".")
    else:
        return f"{n:,}".replace(",", "_").replace(".", ",").replace("_", ".")


def normalize_egg_type(egg_type: str) -> str:
    """Maps legacy egg names to the canonical values used by the cache and DB."""
    mapping = {
        "Schokoei": "Schokoei",
        "cooked": "cooked",
        "gekochtes Hühnerei": "cooked",
        "ungekochtes Hühnerei": "uncooked",
        "uncooked": "uncooked",
    }
    return mapping.get(egg_type, egg_type)


# ----------------------------
# Cache-Modelle
# ----------------------------
@dataclass
class UserRow:
    user_id: str
    last_hit: int = 0
    egg_talisman: int = 0
    rabbit_foot_count: int = 0
    used_rabbit_foot_count: int = 0
    notifications: bool = True
    points: int = 0
    cakes: int = 0
    chocolate_eggs: int = 0
    last_fight: int = 0
    used_collect: int = 0
    found_nests: int = 0
    tickets: int = 0
    eggs_throwen: int = 0
    eggs_hit: int = 0
    eggs_hit_at: int = 0
    eggs_throwen_at: int = 0



@dataclass
class EggRow:
    egg_id: int
    owner_id: str
    creator_id: str
    type: str
    rotten_ts: int


class EggView:
    def __init__(self, row: EggRow, now: float):
        self.id = row.egg_id
        self.owner_id = row.owner_id
        self.creator_id = row.creator_id
        self.type = row.type

        # row.rotten_ts ist "tm.time()" beim Insert
        self.is_rotten = (
            (row.rotten_ts <= now - 3600 and row.type == "uncooked")
            or (row.rotten_ts <= now - 86400 and row.type == "cooked")
        )


# ----------------------------
# Der Handler (Service)
# ----------------------------
class SQLiteCacheDB:
    """
    Dieser Handler ist das Herzstück:
    - DB Verbindung (aiosqlite)
    - Cache (users, eggs, stats)
    - Dirty Tracking + Flush loop
    """

    def __init__(self, bot: discord.Client, db_path: str = "data.db"):
        self.bot = bot
        self.db_path = db_path

        self.log = log_helper.create("SQLiteCacheDB")

        self.db: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
        self._ready = asyncio.Event()

        # ----------------
        # Cache
        # ----------------
        self.users: Dict[str, UserRow] = {}

        # eggs: nach egg_id, plus index nach owner_id für schnellen Zugriff
        self.eggs: Dict[int, EggRow] = {}
        self.eggs_by_owner: Dict[str, Set[int]] = {}

        # stats: key -> value
        self.stats: Dict[str, int] = {}

        # ----------------
        # Dirty tracking
        # ----------------
        self.dirty_users: Set[str] = set()

        # Für eggs unterscheiden wir:
        # - neue eggs (haben temporäre negative egg_id, müssen inserted werden)
        # - deleted eggs (nur IDs)
        # - geänderte eggs (z.B. owner_id geändert, müssen per UPDATE aktualisiert werden)
        self.new_eggs: List[Tuple[int, str, str, str, int]] = []  # (temp_egg_id, owner_id, creator_id, type, rotten_ts)
        self.deleted_eggs: Set[int] = set()
        self.dirty_eggs: Set[int] = set()  # Eggs mit geänderten Feldern (z.B. owner)
        self._next_temp_egg_id: int = -1

        # stats: key -> value (value ist immer int)
        self.dirty_stats: Set[str] = set()

    async def start(self):
        """
        Startet DB, Schema, lädt Cache, startet Flush-Loop.
        Wird in main.py in setup_hook aufgerufen.
        """
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA foreign_keys = ON;")

        await self._init_schema()
        await self._load_cache()

        self.flush_loop.start()
        self._ready.set()

        self.log("SQLiteCacheDB ist bereit!", "SUCCESS")

    async def close(self):
        """
        Stoppt flush_loop, schreibt letzte Änderungen, schließt DB.
        """
        if self.flush_loop.is_running():
            self.flush_loop.cancel()

        await self.flush_dirty()

        if self.db:
            await self.db.close()
            self.db = None

    async def wait_ready(self):
        await self._ready.wait()

    async def _init_schema(self):
        """
        SQLite-kompatibles Schema + Seed Stats.
        """
        assert self.db is not None

        await self.db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            last_hit INTEGER DEFAULT 0,
            egg_talisman INTEGER DEFAULT 0,
            rabbit_foot_count INTEGER DEFAULT 0,
            used_rabbit_foot_count INTEGER DEFAULT 0,
            notifications INTEGER DEFAULT 1,
            points INTEGER DEFAULT 0,
            cakes INTEGER DEFAULT 0,
            chocolate_eggs INTEGER DEFAULT 0,
            last_fight INTEGER DEFAULT 0,
            used_collect INTEGER DEFAULT 0,
            found_nests INTEGER DEFAULT 0,
            tickets INTEGER DEFAULT 0,
            eggs_throwen INTEGER DEFAULT 0,
            eggs_hit INTEGER DEFAULT 0,
            eggs_hit_at INTEGER DEFAULT 0,
            eggs_throwen_at INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS eggs (
            egg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id TEXT,
            creator_id TEXT,
            type TEXT CHECK(type IN ('cooked', 'uncooked')),
            rotten_ts INTEGER,
            FOREIGN KEY (owner_id) REFERENCES users(user_id),
            FOREIGN KEY (creator_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS egg_fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challenger_id TEXT,
            defender_id TEXT,
            chocolate_egg_bet INTEGER,
            winner_id TEXT,
            FOREIGN KEY (challenger_id) REFERENCES users(user_id),
            FOREIGN KEY (defender_id) REFERENCES users(user_id),
            FOREIGN KEY (winner_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS group_fights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participants INTEGER,
            chocolate_egg_bet INTEGER,
            first_place_id TEXT,
            second_place_id TEXT,
            third_place_id TEXT,
            FOREIGN KEY (first_place_id) REFERENCES users(user_id),
            FOREIGN KEY (second_place_id) REFERENCES users(user_id),
            FOREIGN KEY (third_place_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS stats (
            stat TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        );

        INSERT INTO stats(stat, value) VALUES
            ('nests_found', 0),
            ('nests_searched', 0),
            ('deleted_cooked', 0),
            ('deleted_uncooked', 0),
            ('1', 0), ('2', 0), ('3', 0), ('4', 0), ('5', 0)
        ON CONFLICT(stat) DO UPDATE SET value = value;
        """)

        await self.db.commit()

    async def _load_cache(self):
        """
        Lädt users, eggs, stats komplett in den Cache.
        (Wenn das zu groß wird: später auf lazy load umstellen.)
        """
        assert self.db is not None

        # ---- users
        self.users.clear()
        async with self.db.execute("""
            SELECT user_id, last_hit, egg_talisman, rabbit_foot_count, used_rabbit_foot_count,
                   notifications, points, cakes, chocolate_eggs, last_fight, used_collect, found_nests, tickets, eggs_throwen, eggs_hit, eggs_hit_at, eggs_throwen_at
            FROM users
        """) as cur:
            rows = await cur.fetchall()

        for r in rows:
            self.users[r[0]] = UserRow(
                user_id=r[0],
                last_hit=r[1],
                egg_talisman=r[2],
                rabbit_foot_count=r[3],
                used_rabbit_foot_count=r[4],
                notifications=bool(r[5]),
                points=r[6],
                cakes=r[7],
                chocolate_eggs=r[8],
                last_fight=r[9],
                used_collect=r[10],
                found_nests=r[11],
                tickets=r[12],
                eggs_throwen=r[13],
                eggs_hit=r[14],
                eggs_hit_at=r[15],
                eggs_throwen_at=r[16]
            )

        # ---- eggs + index
        self.eggs.clear()
        self.eggs_by_owner.clear()
        async with self.db.execute("SELECT egg_id, owner_id, creator_id, type, rotten_ts FROM eggs") as cur:
            egg_rows = await cur.fetchall()

        for e in egg_rows:
            row = EggRow(egg_id=e[0], owner_id=e[1], creator_id=e[2], type=normalize_egg_type(e[3]), rotten_ts=e[4])
            self.eggs[row.egg_id] = row
            self.eggs_by_owner.setdefault(row.owner_id, set()).add(row.egg_id)

        # ---- stats
        self.stats.clear()
        async with self.db.execute("SELECT stat, value FROM stats") as cur:
            stat_rows = await cur.fetchall()
        for s in stat_rows:
            self.stats[s[0]] = int(s[1])

    # -------------------------
    # Flush: dirty -> SQLite
    # -------------------------
    async def flush_dirty(self):
        """
        Schreibt:
        - dirty users per Upsert
        - new eggs Inserts
        - deleted eggs Deletes
        - dirty eggs Updates (z.B. owner_id Änderungen)
        - dirty stats Upserts
        Alles in 1 Transaktion (BEGIN/COMMIT).
        """
        await self.wait_ready()
        assert self.db is not None

        # Snapshot unter Lock ziehen, damit wir schnell wieder frei sind
        async with self._lock:
            dirty_user_ids = list(self.dirty_users)
            self.dirty_users.clear()
            users_payload = [self.users[uid] for uid in dirty_user_ids if uid in self.users]

            new_eggs_payload = list(self.new_eggs)
            self.new_eggs.clear()

            deleted_eggs_payload = list(self.deleted_eggs)
            self.deleted_eggs.clear()

            dirty_eggs_ids = list(self.dirty_eggs)
            self.dirty_eggs.clear()
            dirty_eggs_payload = [self.eggs[eid] for eid in dirty_eggs_ids if eid in self.eggs]

            dirty_stats_keys = list(self.dirty_stats)
            self.dirty_stats.clear()
            stats_payload = [(k, self.stats.get(k, 0)) for k in dirty_stats_keys]

        if not users_payload and not new_eggs_payload and not deleted_eggs_payload and not dirty_eggs_payload and not stats_payload:
            return  # nix zu tun

        await self.db.execute("BEGIN;")
        try:
            # ---- users upsert
            if users_payload:
                await self.db.executemany("""
                    INSERT INTO users(
                        user_id, last_hit, egg_talisman, rabbit_foot_count, used_rabbit_foot_count,
                        notifications, points, cakes, chocolate_eggs, last_fight, used_collect, found_nests,
                        tickets, eggs_throwen, eggs_hit, eggs_hit_at, eggs_throwen_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        last_hit=excluded.last_hit,
                        egg_talisman=excluded.egg_talisman,
                        rabbit_foot_count=excluded.rabbit_foot_count,
                        used_rabbit_foot_count=excluded.used_rabbit_foot_count,
                        notifications=excluded.notifications,
                        points=excluded.points,
                        cakes=excluded.cakes,
                        chocolate_eggs=excluded.chocolate_eggs,
                        last_fight=excluded.last_fight,
                        used_collect=excluded.used_collect,
                        found_nests=excluded.found_nests,
                        tickets=excluded.tickets,
                        eggs_throwen=excluded.eggs_throwen,
                        eggs_hit=excluded.eggs_hit,
                        eggs_hit_at=excluded.eggs_hit_at,
                        eggs_throwen_at=excluded.eggs_throwen_at;
                        
                """, [
                    (
                        u.user_id,
                        u.last_hit,
                        u.egg_talisman,
                        u.rabbit_foot_count,
                        u.used_rabbit_foot_count,
                        1 if u.notifications else 0,
                        u.points,
                        u.cakes,
                        u.chocolate_eggs,
                        u.last_fight,
                        u.used_collect,
                        u.found_nests,
                        u.tickets,
                        u.eggs_throwen,
                        u.eggs_hit,
                        u.eggs_hit_at,
                        u.eggs_throwen_at
                    )
                    for u in users_payload
                ])

            # ---- eggs inserts (AUTOINCREMENT ids)
            if new_eggs_payload:
                # Wir inserten einzeln, damit wir lastrowid bekommen (und den Cache korrekt halten)
                for (temp_egg_id, owner_id, creator_id, egg_type, rotten_ts) in new_eggs_payload:
                    egg_type = normalize_egg_type(egg_type)
                    cur = await self.db.execute(
                        "INSERT INTO eggs(owner_id, creator_id, type, rotten_ts) VALUES (?, ?, ?, ?)",
                        (owner_id, creator_id, egg_type, rotten_ts),
                    )
                    egg_id = cur.lastrowid

                    # Temporären Cache-Eintrag durch persistierten Eintrag ersetzen.
                    async with self._lock:
                        temp_row = self.eggs.pop(int(temp_egg_id), None)
                        if temp_row:
                            self.eggs_by_owner.get(temp_row.owner_id, set()).discard(int(temp_egg_id))

                        row = EggRow(
                            egg_id=int(egg_id),
                            owner_id=owner_id,
                            creator_id=creator_id,
                            type=egg_type,
                            rotten_ts=rotten_ts,
                        )
                        self.eggs[row.egg_id] = row
                        self.eggs_by_owner.setdefault(owner_id, set()).add(row.egg_id)

            # ---- eggs updates (z.B. owner_id Änderungen)
            if dirty_eggs_payload:
                await self.db.executemany(
                    "UPDATE eggs SET owner_id = ?, creator_id = ?, type = ?, rotten_ts = ? WHERE egg_id = ?",
                    [(e.owner_id, e.creator_id, e.type, e.rotten_ts, e.egg_id) for e in dirty_eggs_payload]
                )

            # ---- eggs deletes
            if deleted_eggs_payload:
                await self.db.executemany("DELETE FROM eggs WHERE egg_id = ?", [(eid,) for eid in deleted_eggs_payload])

            # ---- stats upsert
            if stats_payload:
                await self.db.executemany("""
                    INSERT INTO stats(stat, value) VALUES (?, ?)
                    ON CONFLICT(stat) DO UPDATE SET value=excluded.value;
                """, stats_payload)

            await self.db.commit()

        except Exception:
            await self.db.rollback()
            raise

        self.log("Flush complete", "SYSTEM")    
        #self.log(f"Flush complete: {len(users_payload)} users, {len(new_eggs_payload)} new eggs, {len(dirty_eggs_payload)} updated eggs, {len(deleted_eggs_payload)} deleted eggs, {len(stats_payload)} stats.", "DEBUG")


    @tasks.loop(minutes=1)
    async def flush_loop(self):
        """
        Hintergrund-Loop: speichert alle 5 Minuten.
        Falls ein Fehler passiert, wird er geloggt, aber der Loop läuft weiter (nächster Versuch in 5 Minuten).
         - z.B. könnte die DB temporär nicht erreichbar sein, oder es gibt einen Fehler im Flush-Code, der erstmal behoben werden muss.
        """
        try:
            await self.flush_dirty()
        except Exception as e:
            self.log(f"DB Flush Fehler: {e}", "ERROR")

    @flush_loop.before_loop
    async def before_flush(self):
        # wartet, bis Bot ready (Login abgeschlossen) ist
        await self.bot.wait_until_ready()

    # -------------------------
    # User-Operationen (Cache)
    # -------------------------
    async def get_or_create_user(self, user_id: int) -> UserRow:
        await self.wait_ready()
        uid = str(user_id)

        async with self._lock:
            u = self.users.get(uid)
            if u:
                return u

            # neu im Cache anlegen (wird später per Upsert gespeichert)
            u = UserRow(user_id=uid)
            self.users[uid] = u
            self.dirty_users.add(uid)
            return u

    # -------------------------
    # Egg-Operationen (Cache)
    # -------------------------
    async def eggs_of_owner(self, owner_id: int) -> List[EggView]:
        await self.wait_ready()
        oid = str(owner_id)
        now = tm.time()

        async with self._lock:
            ids = list(self.eggs_by_owner.get(oid, set()))
            rows = [self.eggs[eid] for eid in ids if eid in self.eggs]

        # "View" bauen (rotten berechnen)
        eggs = [EggView(r, now) for r in rows]
        eggs.sort(key=lambda x: x.id)
        return eggs

    async def eggs_of_owner_by_type(self, owner_id: int, egg_type: str) -> List[EggView]:
        eggs = await self.eggs_of_owner(owner_id)
        return [e for e in eggs if e.type == egg_type]

    async def egg_by_id(self, egg_id: int) -> Optional[EggView]:
        await self.wait_ready()
        now = tm.time()
        async with self._lock:
            row = self.eggs.get(int(egg_id))
        return EggView(row, now) if row else None

    async def queue_new_egg(self, owner_id: int, creator_id: int, egg_type: str):
        """
        Legt ein neues Egg an, aber schreibt es nicht sofort in DB:
        - wird gequeued in self.new_eggs
        - beim Flush wird es inserted und dann in Cache übernommen (mit egg_id)
        """
        await self.wait_ready()

        await self.get_or_create_user(owner_id)
        if creator_id != owner_id:
            await self.get_or_create_user(creator_id)

        oid = str(owner_id)
        cid = str(creator_id)
        ts = int(tm.time())
        egg_type = normalize_egg_type(egg_type)

        async with self._lock:
            temp_id = self._next_temp_egg_id
            self._next_temp_egg_id -= 1

            row = EggRow(
                egg_id=temp_id,
                owner_id=oid,
                creator_id=cid,
                type=egg_type,
                rotten_ts=ts,
            )
            self.eggs[row.egg_id] = row
            self.eggs_by_owner.setdefault(oid, set()).add(row.egg_id)
            self.new_eggs.append((temp_id, oid, cid, egg_type, ts))

    async def set_egg_owner(self, egg_id: int, new_owner_id: int):
        """
        Ändert owner im Cache sofort und markiert das Egg als dirty für den nächsten Flush.
        Die DB wird asynchron beim nächsten Flush aktualisiert.
        """
        await self.wait_ready()
        new_oid = str(new_owner_id)
        
        async with self._lock:
            row = self.eggs.get(int(egg_id))
            if not row:
                return
            
            old_owner = row.owner_id
            row.owner_id = new_oid

            # index anpassen
            if old_owner in self.eggs_by_owner:
                self.eggs_by_owner[old_owner].discard(row.egg_id)
            self.eggs_by_owner.setdefault(new_oid, set()).add(row.egg_id)
            
            # Egg als dirty markieren für Flush
            if row.egg_id > 0:  # nur wenn bereits in DB vorhanden (nicht temp)
                self.dirty_eggs.add(row.egg_id)

    async def delete_egg(self, egg_id: int):
        """
        Entfernt Egg aus Cache und queue't Delete für nächsten Flush.
        """
        await self.wait_ready()
        eid = int(egg_id)

        async with self._lock:
            row = self.eggs.pop(eid, None)
            if row:
                self.eggs_by_owner.get(row.owner_id, set()).discard(eid)

            if eid < 0:
                # Noch nicht persistiert: nur aus Insert-Queue entfernen.
                self.new_eggs = [entry for entry in self.new_eggs if int(entry[0]) != eid]
            else:
                # Bereits in DB vorhanden: Delete für nächsten Flush vormerken.
                self.deleted_eggs.add(eid)

    # -------------------------
    # Stats (Cache)
    # -------------------------
    async def stats_inc(self, key: str, amount: int = 1):
        await self.wait_ready()
        async with self._lock:
            self.stats[key] = int(self.stats.get(key, 0)) + amount
            self.dirty_stats.add(key)


# ------------------------------------------------------
# "Alte" Klassenstruktur (Facade) um den Handler herum
# ------------------------------------------------------
class Database:
    """
    Hier gibt es statische Methoden, die von außen aufgerufen werden (z.B. in game.py).
    Diese Methoden greifen auf den Handler zu, der im Cache-Modus läuft.
    """
    handler: Optional[SQLiteCacheDB] = None

    @staticmethod
    def set_handler(handler: SQLiteCacheDB):
        Database.handler = handler


class Get:
    @staticmethod
    async def user(id):
        assert Database.handler is not None
        return await Database.handler.get_or_create_user(id)
    
    @staticmethod
    async def probailities(id):
        talisman = await Get.talisman_type(id)

        cooked = 0.577 if talisman == 0 else 0.677 if talisman == 1 else 0.477
        uncooked = round(0.873 - cooked, 3)

        return (cooked, uncooked)
    
    @staticmethod
    async def points(id):
        chocolate_eggs = await Get.user(id)
        chocolate_eggs = chocolate_eggs.chocolate_eggs

        user = await Get.user(id)        
        cakes = user.cakes
        points = chocolate_eggs + cakes * 10

        #update points in cache (wird später beim Flush in DB geschrieben)
        u = await Get.user(id)
        u.points = points
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

        return points



    @staticmethod
    async def eggs(id):
        assert Database.handler is not None
        return await Database.handler.eggs_of_owner(id)

    @staticmethod
    async def type_eggs(id, type):
        assert Database.handler is not None
        return await Database.handler.eggs_of_owner_by_type(id, normalize_egg_type(type))

    @staticmethod
    async def type_eggs_not_rotten(id, type):
        eggs = await Get.type_eggs(id, type)
        return [egg for egg in eggs if egg.is_rotten is False]

    @staticmethod
    async def egg(id):
        assert Database.handler is not None
        return await Database.handler.egg_by_id(id)

    @staticmethod
    async def egg_check(id, type):
        eggs = await Get.eggs(id)
        type = normalize_egg_type(type)
        for egg in eggs:
            if egg.type == type and egg.is_rotten is False:
                return egg
        return False

    @staticmethod
    async def bake_check(id):
        eggs = await Get.eggs(id)
        chocolate_eggs = (await Get.user(id)).chocolate_eggs
        uncooked_eggs = len([e for e in eggs if normalize_egg_type(e.type) == "uncooked" and e.is_rotten is False])
        return chocolate_eggs >= 10 and uncooked_eggs >= 3

    @staticmethod
    async def notifications(id):
        u = await Get.user(id)
        return bool(u.notifications)

    @staticmethod
    async def rabbit_foot_amount(id):
        u = await Get.user(id)
        return u.rabbit_foot_count

    @staticmethod
    async def used_rabbit_foot_amount(id):
        u = await Get.user(id)
        return u.used_rabbit_foot_count

    @staticmethod
    async def user_collect_amount(id):
        u = await Get.user(id)
        return u.used_collect

    @staticmethod
    async def user_found_nests(id):
        u = await Get.user(id)
        return u.found_nests

    @staticmethod
    async def talisman_check(id):
        u = await Get.user(id)
        return False if u.egg_talisman > 0 else True

    @staticmethod
    async def talisman_type(id):
        u = await Get.user(id)
        return u.egg_talisman
    
    @staticmethod
    async def probabilities(id):
        talisman = await Get.talisman_type(id)
        cooked = 0.577 if talisman == 0 else 0.677 if talisman == 1 else 0.477
        uncooked = round(0.873 - cooked, 3)
        return (cooked, uncooked)

    @staticmethod
    def throw_percent(points):
        # rein logisch, kein DB Zugriff -> kann sync bleiben
        if points <= 30:
            return random.randint(20, 50)
        elif points <= 150:
            return random.randint(7, 20)
        else:
            return random.randint(2, 7)

    @staticmethod
    async def tickets(id):
        u = await Get.user(id)
        return u.tickets
    
    @staticmethod
    async def top_position(id):
        assert Database.handler is not None
        await Database.handler.wait_ready()

        users = list(Database.handler.users.values())
        users.sort(key=lambda u: u.points, reverse=True)

        for i, u in enumerate(users, start=1):
            if u.user_id == str(id):
                return i
        return None


class Add:
    @staticmethod
    async def user(id):
        """
        Im neuen System: get_or_create_user legt User im Cache an und markiert dirty.
        """
        await Get.user(id)

    @staticmethod
    async def tickets(id, amount):
        u = await Get.user(id)
        # delete one cooked egg pro ticket
        for _ in range(amount):
            eggs = await Get.type_eggs_not_rotten(id, "cooked")
            if not eggs:
                break
            egg_to_delete = eggs[0]
            await Database.handler.delete_egg(egg_to_delete.id)
        u.tickets += amount
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def cake(id, nested=False):
        u = await Get.user(id)
        u.cakes += 1
        if not nested:
            u.chocolate_eggs -= 10

        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

        if not nested:

            eggs = await Get.type_eggs_not_rotten(id, "uncooked")
            for i in range(min(3, len(eggs))):
                egg_to_delete = eggs[i]
                await Database.handler.delete_egg(egg_to_delete.id)

    @staticmethod
    async def multiple_eggs(id, egg_type, amount):
        for _ in range(amount):
            await Add.egg(id, egg_type)

    @staticmethod
    async def egg(id, type):
        """
        Queued ein neues Egg. egg_id entsteht erst beim Flush (AUTOINCREMENT).
        """
        assert Database.handler is not None
        type = normalize_egg_type(type)
        if type == "Schokoei":
        # update cholate_eggs in the user cache (wird später beim Flush in DB geschrieben)
            u = await Get.user(id)
            u.chocolate_eggs += 1
            assert Database.handler is not None
            async with Database.handler._lock:
                Database.handler.dirty_users.add(u.user_id)
            return
        await Database.handler.queue_new_egg(owner_id=id, creator_id=id, egg_type=type)

    @staticmethod
    async def throw(thrower_id, defender_id, success):
        thrower = await Get.user(thrower_id)
        defender = await Get.user(defender_id)

        thrower.eggs_throwen += 1
        defender.eggs_throwen_at
        if success:
            defender.eggs_hit
            thrower.eggs_hit_at += 1

        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(thrower.user_id)
            Database.handler.dirty_users.add(defender.user_id)


    @staticmethod
    async def solo_fight(challenger_id, defender_id, chocolate_egg_bet, winner_id):
        challenger = await Get.user(challenger_id)
        defender = await Get.user(defender_id)
        winner = await Get.user(winner_id)

        # Bet abziehen
        challenger.chocolate_eggs -= chocolate_egg_bet
        defender.chocolate_eggs -= chocolate_egg_bet

        # Gewinn auszahlen
        winner.chocolate_eggs += chocolate_egg_bet * 2

        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(challenger.user_id)
            Database.handler.dirty_users.add(defender.user_id)
            Database.handler.dirty_users.add(winner.user_id)
    


class Update:
    @staticmethod
    async def user_last_hit(id):
        u = await Get.user(id)
        u.last_hit = int(tm.time())
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def user_egg_talisman(id, egg_talisman):
        u = await Get.user(id)
        u.egg_talisman = int(egg_talisman)
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def user_add_one_rabbit_foot_count(id):
        u = await Get.user(id)
        u.rabbit_foot_count += 1
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def user_remove_one_rabbit_foot_count(id):
        u = await Get.user(id)
        u.rabbit_foot_count -= 1
        u.used_rabbit_foot_count += 1
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def egg_owner(id, owner_id):
        """
        Bei dir: Update eggs SET owner_id = ...
        Hier: Cache + DB Update (der Teil ist aktuell "sofort", siehe Handler-Kommentar).
        """
        assert Database.handler is not None
        await Database.handler.set_egg_owner(id, owner_id)

    @staticmethod
    async def user_notifications(id, notifications):
        u = await Get.user(id)
        u.notifications = bool(notifications)
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def last_fight(id):
        u = await Get.user(id)
        u.last_fight = int(tm.time())
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def reset_last_fight(id):
        u = await Get.user(id)
        u.last_fight = 0
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)
        await Add.egg(id, "cooked")

    @staticmethod
    async def user_add_collect(id):
        u = await Get.user(id)
        u.used_collect += 1
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    @staticmethod
    async def user_add_found_nests(id):
        u = await Get.user(id)
        u.found_nests += 1
        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(u.user_id)

    # stats-Updates: im Cache inkrementieren (dirty_stats)
    @staticmethod
    async def stats_location(location):
        assert Database.handler is not None
        await Database.handler.stats_inc(location, 1)
        await Update.stats_add_nests_searched()

    @staticmethod
    async def stats_add_nests_found():
        assert Database.handler is not None
        await Database.handler.stats_inc("nests_found", 1)

    @staticmethod
    async def stats_add_nests_searched():
        assert Database.handler is not None
        await Database.handler.stats_inc("nests_searched", 1)

    @staticmethod
    async def stats_deleted_cooked():
        assert Database.handler is not None
        await Database.handler.stats_inc("deleted_cooked", 1)

    @staticmethod
    async def stats_deleted_uncooked():
        assert Database.handler is not None
        await Database.handler.stats_inc("deleted_uncooked", 1)

    @staticmethod
    async def leaderboard(top):
        assert Database.handler is not None
        await Database.handler.wait_ready()

        users = list(Database.handler.users.values())
        for u in users:
            u.points = await Get.points(u.user_id)


class Gen:
    @staticmethod
    async def nest(location, ctx, rabbit_foot):
        if rabbit_foot != 0:
            rabbit_foot = True
        class Nest:
            def __init__(self, location, type, schokoei=0, gekochtesEi=0, ungekochtesEi=0, egg_talisman=0, rabbit_foot_count=0, cakes=0):
                self.location = location
                self.type = type
                self.schokoei = schokoei
                self.gekochtesEi = gekochtesEi
                self.ungekochtesEi = ungekochtesEi
                self.egg_talisman = egg_talisman
                self.rabbit_foot_count = rabbit_foot_count
                self.cakes = cakes

        probabilities = await Get.probabilities(ctx.author.id)
        type = random.choices(["empty", "normal", "special"], weights=[0.25, 0.7, 0.05])[0]
        if type == "empty":
            return Nest(location=location, type="empty")
        elif type == "normal":
            return Nest(location=location, type="normal",
                                                   schokoei=random.randint(1, 10) * (2 if rabbit_foot else 1),
                                                   gekochtesEi=0 if random.random() < probabilities[0] else (random.randint(1, 2) * (2 if rabbit_foot else 1)),
                                                   ungekochtesEi=0 if random.random() < probabilities[1] else (random.randint(1, 2) * (2 if rabbit_foot else 1)))
        elif type == "special":
            return Nest(location=location, type="special",
                                                   schokoei=random.randint(5, 15) * (2 if rabbit_foot else 1),
                                                   gekochtesEi=0 if random.random() < probabilities[0] else (random.randint(2, 4) * (2 if rabbit_foot else 1)),
                                                   ungekochtesEi=0 if random.random() < probabilities[1] else (random.randint(2, 4) * (2 if rabbit_foot else 1)),
                                                   egg_talisman=1 if await Get.talisman_check(ctx.author.id) and random.random() <= 0.27 else 0,
                                                   rabbit_foot_count=1 * (2 if rabbit_foot else 1) if random.random() <= 0.395 else 0,
                                                   cakes=1 * (2 if rabbit_foot else 1) if random.random() <= 0.5 else 0)
        
    def solo_fight_text(winner, loser, chocolate_egg_bet, participants):
        strig = random.choice(["Die beiden Eier scheinen einiges auszuhalten.",
                      "Beide sind hochkonzentriert am Eier aufeinanderschlagen.",
                      "Keines der Eier scheint so richtig nachzugeben.",
                      "Eieiei, was passiert denn da?",
                      "Ein Ei gleicht dem anderen - noch kann sich keiner durchsetzen.",
                      f"Ist das etwa ein Sprung im Ei von <@{random.choice(participants)}>? Noch hat keiner gewonnen...",
                      "Kein Ei-nfaches Duell, es will sich keiner so richtig durchsetzen.",
                      "Möge das beste Ei gewinnen!",
                      "Spannung liegt in der Luft, während sich unsere beiden Kontrahenten duellieren.",
                      "Ei-nfach spannend!",
                      "Das ist ein Kopf-an-Kopf-Rennen! Oder doch Ei an Ei?",
                      "Es ist ein Hin und Her zwischen den beiden. Wer wird am Ende triumphieren?",
                      "Wer hat das härtere Ei? Noch wirken beide sehr solide.",
                      "Die Spannung steigt, während die Eier aufeinanderprallen.",
                      "Es sieht aus, als ob keiner der beiden nachgeben möchte.",
                      "Ein episches Duell der Eier, das seinesgleichen sucht.",
                      "Die Zuschauer halten den Atem an, während die Eier aufeinander treffen.",
                      "Ein wahres Spektakel! Beide Eier scheinen unzerstörbar.",
                      "Die Kontrahenten schenken sich nichts, das Duell bleibt spannend.",
                      "Ein Schlag nach dem anderen, doch noch ist kein Sieger in Sicht.",
                      "Die Eier scheinen aus Stahl zu sein, keiner gibt nach.",
                      "Ein Duell, das in die Geschichte eingehen wird. Wer wird gewinnen?",
                      "Die Spannung ist kaum auszuhalten, beide Eier sind noch intakt.",
                      "Ein wahres Kopf-an-Kopf-Rennen, die Entscheidung steht noch aus.",
                      "Wer hat das härtere Ei? Noch wirken beide sehr solide.",
                      "Es sieht aus, als ob keiner der beiden nachgeben möchte.",])
        return strig
    
    def group_fight_text(participants):
        string = random.choice(["Die Eier scheinen einiges auszuhalten",
                    "Keines der Eier scheint so richtig nachzugeben.",
                    "Eieiei, was passiert denn da?",
                    "Ein Ei gleicht dem anderen - noch kann sich keiner durchsetzen.",
                    f"Ist das etwa ein Sprung im Ei von <@{random.choice(participants)}>? Noch hat keiner gewonnen...",
                    "Kein Ei-nfaches Duell, es will sich keiner so richtig durchsetzen.",
                    "Möge das beste Ei gewinnen!",
                    "Ei-nfach spannend!",
                    "Das ist ein Kopf-an-Kopf-Rennen! Oder doch Ei an Ei?",
                    "Die Spannung steigt, während die Eier aufeinanderprallen.",
                    "Ein episches Duell der Eier, das seinesgleichen sucht.",
                    "Die Zuschauer halten den Atem an, während die Eier aufeinander treffen.",
                    "Ein wahres Spektakel! Beide Eier scheinen unzerstörbar.",
                    "Die Kontrahenten schenken sich nichts, das Duell bleibt spannend.",
                    "Ein Schlag nach dem anderen, doch noch ist kein Sieger in Sicht.",
                    "Die Eier scheinen aus Stahl zu sein, keiner gibt nach.",
                    "Ein Duell, das in die Geschichte eingehen wird. Wer wird gewinnen?",
                    "Die Spannung ist kaum auszuhalten, beide Eier sind noch intakt.",
                    "Ein wahres Kopf-an-Kopf-Rennen, die Entscheidung steht noch aus.",
                    "Wer hat das härtere Ei? Noch wirken beide sehr solide.",
                    "Es sieht aus, als ob keiner der beiden nachgeben möchte.",
                    "Ein Schlagabtausch der Extraklasse, die Eier prallen immer wieder aufeinander.",
                    "Die Menge tobt, während die Eier aufeinanderkrachen.",
                    "Ein Duell, das die Zuschauer in Atem hält.",
                    "Die Eier scheinen unzerstörbar, doch wer wird am Ende triumphieren?",
                    "Die Spannung ist greifbar, während die Eier aufeinander treffen.",])
        
        return string
    
    def group_fight_loose_text(looser):
        string = random.choice([f"Das Ei von <@{looser}> gibt nach, das wars!",
                    f"Knacks, das Ei ist kaputt, <@{looser}> ist raus!",
                    f"Ziemlich hart, nich so fair - <@{looser}> ist ausgeschieden.",
                    f"Plitsch, platsch, das Ei is matsch. Damit ist <@{looser}> raus.",
                    f"Das waren wohl keine Eier aus Stahl. Sorry <@{looser}>, du bist drausen.",
                    f"Eieiei, warum vorbei? Tut mir Leid <@{looser}>, aber dein Ei hat nachgegeben.",
                    f"Ein harter Schlag, und das Ei von <@{looser}> zerbricht in tausend Stücke.",
                    f"Das war's für <@{looser}>! Sein Ei hat den Druck nicht ausgehalten.",
                    f"Ein lautes Knacken, und <@{looser}> ist aus dem Rennen.",
                    f"Das Ei von <@{looser}> hat den Kürzeren gezogen. Aus und vorbei!",
                    f"Ein trauriger Moment für <@{looser}> - sein Ei ist Geschichte.",
                    f"Das Ei von <@{looser}> hat den Kampf nicht überlebt. Besseres Glück beim nächsten Mal!",
                    f"Ein letzter Schlag, und das Ei von <@{looser}> zerbricht. Das war's!",
                    f"Das Ei von <@{looser}> hat den Geist aufgegeben. Ein harter Verlust!",
                    f"Ein lautes Plopp, und <@{looser}> ist raus aus dem Spiel.",
                    f"Das Ei von <@{looser}> hat den Druck nicht überstanden. Schade!",
                    f"Ein harter Treffer, und das Ei von <@{looser}> ist Geschichte.",
                    f"Das war ein harter Schlag! <@{looser}> ist ausgeschieden.",
                    f"Das Ei von <@{looser}> hat den Kampf verloren. Vielleicht nächstes Mal!",
                    f"Ein letzter Schlag, und das Ei von <@{looser}> zerbricht. Das war's!",
                    f"Das Ei von <@{looser}> hat den Geist aufgegeben. Ein harter Verlust!",
                    f"Ein lautes Plopp, und <@{looser}> ist raus aus dem Spiel.",
                    f"Das Ei von <@{looser}> hat den Druck nicht überstanden. Schade!",
                    f"Ein harter Treffer, und das Ei von <@{looser}> ist Geschichte.",
                    f"Das war ein harter Schlag! <@{looser}> ist ausgeschieden.",])
        return string
    
    def throw_text(success, defender, percent=None, reward=None):
        if success:
            string = random.choice([f"Du hast ein :egg: auf <@{defender.user_id}> geworfen und getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!",
                        f"Volltreffer! Dein :egg: hat <@{defender.user_id}> getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!",
                        f"Dein Wurf war erfolgreich! <@{defender.user_id}> wurde getroffen! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!",
                        f"Treffer! Dein :egg: hat <@{defender.user_id}> erwischt! Du hast {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` erhalten!",
                        f"Du hast <@{defender.user_id}> mit deinem :egg: getroffen! {reward}x <:Schoko_Ei:1221556659030196284>`{percent}%` für dich!",])
        else:
            string = random.choice([f"Leider hast du <@{defender.user_id}> mit deinem :egg: verfehlt. Schade!",
                        f"Dein Wurf ging daneben, <@{defender.user_id}> ist nicht getroffen worden.",
                        f"Leider kein Treffer! <@{defender.user_id}> bleibt verschont.",
                        f"Dein :egg: hat sein Ziel verfehlt, <@{defender.user_id}> ist nicht getroffen worden.",
                        f"Schade, dein Wurf war nicht erfolgreich. <@{defender.user_id}> bleibt unversehrt.",])
        return string



class Delete:
    @staticmethod
    async def egg(id):
        """
        Löscht Egg aus Cache und queued DB delete.
        Zusätzlich Stats inkrementieren
        """
        egg = await Get.egg(id)
        assert Database.handler is not None

        await Database.handler.delete_egg(id)

        if egg:
            egg_type = normalize_egg_type(egg.type)
            if egg_type == "cooked":
                await Update.stats_deleted_cooked()
            elif egg_type == "uncooked":
                await Update.stats_deleted_uncooked()


class Transfer:
    @staticmethod
    async def chocolate_eggs(from_id, to_id, amount):
        from_user = await Get.user(from_id)
        to_user = await Get.user(to_id)

        if from_user.chocolate_eggs < amount:
            raise ValueError("Nicht genug Schokoeier zum Transferieren.")

        from_user.chocolate_eggs -= amount
        to_user.chocolate_eggs += amount

        assert Database.handler is not None
        async with Database.handler._lock:
            Database.handler.dirty_users.add(from_user.user_id)
            Database.handler.dirty_users.add(to_user.user_id)


# ------------------------------------------------------
# Translate
# ------------------------------------------------------
class Translate:
    @staticmethod
    async def nest(nest):
        if nest.type == "empty":
            return "Luft"
        else:
            nest_info = ""
            if nest.schokoei != 0:
                nest_info += f"{nest.schokoei}x <:Schoko_Ei:1221556659030196284>\n"
            if nest.gekochtesEi != 0:
                nest_info += f"{nest.gekochtesEi}x <:osterei:962802014226640996>\n"
            if nest.ungekochtesEi != 0:
                nest_info += f"{nest.ungekochtesEi}x :egg:\n"
            if nest.egg_talisman != 0:
                nest_info += f"Eier Talisman\n"
            if nest.rabbit_foot_count != 0:
                nest_info += f"{nest.rabbit_foot_count}x Hasenpfote\n"
            if nest.cakes != 0:
                nest_info += f"{nest.cakes}x Kuchen\n"
            return nest_info.strip()
        

    @staticmethod
    async def leaderboard(top):
        assert Database.handler is not None
        await Database.handler.wait_ready()

        async with Database.handler._lock:
            users = list(Database.handler.users.values())

        # Filter wie früher (111111...)
        users = [u for u in users if u.user_id != "111111111111111111"]
        users.sort(key=lambda u: u.points, reverse=True)

        users = users[:top]
        string = ""
        for i, user in enumerate(users):
            string += f"{i+1}. <@{user.user_id}> - {format_number(user.points)}\n"
        return string.strip()