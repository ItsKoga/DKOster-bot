import os

import time as tm

import mysql.connector
from mysql.connector import Error

class Database:

    def connect():
        class Connection:
            def __init__(self):
                self.connection = None
                self.cursor = None
                self.connected = False

            def __enter__(self):
                try:
                    self.connection = mysql.connector.connect(
                        host=os.getenv("DB_HOST"),
                        user=os.getenv("DB_USER"),
                        passwd=os.getenv("DB_PASSWORD"),
                        database=os.getenv("DB_NAME")
                    )
                    self.cursor = self.connection.cursor()
                    self.connected = True
                    return self
                except Error as e:
                    print(f"Error while connecting to the database: {e}")
                    return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if self.connected:
                    self.connection.commit()
                    self.cursor.close()
                    self.connection.close()
                    self.connected = False

        return Connection()
    
    def execute_and_fetchall(query, values=None):
        with Database.connect() as connection:
            if connection.connected:
                if values:
                    connection.cursor.execute(query, values)
                else:
                    connection.cursor.execute(query)
                return connection.cursor.fetchall()
            else:
                return None
            
    def execute_and_commit(query, values=None):
        with Database.connect() as connection:
            if connection.connected:
                if values:
                    connection.cursor.execute(query, values)
                else:
                    connection.cursor.execute(query)
                connection.connection.commit()
                return connection.cursor.fetchall()
            else:
                return None
            
    def execute_and_fetchone(query, values=None):
        with Database.connect() as connection:
            if connection.connected:
                if values:
                    connection.cursor.execute(query, values)
                else:
                    connection.cursor.execute(query)
                return connection.cursor.fetchone()
            else:
                return None
            

class Get:
    def user(id):
        class User:
            def __init__(self, id, last_hit, egg_talisman, rabbit_foot_count, used_rabbit_foot_count):
                self.id = id
                self.last_hit = last_hit
                self.egg_talisman = egg_talisman
                self.rabbit_foot_count = rabbit_foot_count
                self.used_rabbit_foot_count = used_rabbit_foot_count

        user = Database.execute_and_fetchone("SELECT * FROM users WHERE user_id = %s", (id,))
        if user:
            return User(user[0], user[1], user[2], user[3], user[4])
        else:
            Add.user(id)
            return User(id, 0, 0, 0, 0)
        
    def points(id):
        #get amout of chocolate eggs
        chocolate_eggs = 0
        for egg in Get.eggs(id):
            if egg.type == "Schokoei":
                chocolate_eggs += 1
        return chocolate_eggs
        
    def egg(id):
        class Egg:
            def __init__(self, id, owner_id, creator_id, type, is_rotten, time):
                self.id = id
                self.owner_id = owner_id
                self.creator_id = creator_id
                self.type = type
                self.is_rotten = True if (is_rotten <= time-3600 and type == "ungekochtes Hühnerei" or is_rotten <= time-28800 and type == "gekochtes Hühnerei") else False
        egg = Database.execute_and_fetchone("SELECT * FROM eggs WHERE owner_id = %s", (id,))
        time = tm.time()
        if egg:
            return Egg(egg[0], egg[1], egg[2], egg[3], egg[4], time)
        else:
            return None
        
    def solo_fights(id):
        class SoloFight:
            def __init__(self, id, challenger_id, defender_id, chocolate_egg_bet, winner_id):
                self.id = id
                self.challenger_id = challenger_id
                self.defender_id = defender_id
                self.chocolate_egg_bet = chocolate_egg_bet
                self.winner_id = winner_id
        solo_fights = Database.execute_and_fetchall("SELECT * FROM egg_fights WHERE challenger_id = %s OR defender_id = %s", (id, id))
        if solo_fights:
            return [SoloFight(solo_fight[0], solo_fight[1], solo_fight[2], solo_fight[3], solo_fight[4]) for solo_fight in solo_fights]
        else:
            return None
        
    def group_fight(id):
        class GroupFight:
            def __init__(self, id, participants, chocolate_egg_bet, first_place_id, second_place_id, third_place_id):
                self.id = id
                self.participants = participants
                self.chocolate_egg_bet = chocolate_egg_bet
                self.first_place_id = first_place_id
                self.second_place_id = second_place_id
                self.third_place_id = third_place_id
        group_fights = Database.execute_and_fetchall("SELECT * FROM group_fights WHERE first_place_id = %s OR second_place_id = %s OR third_place_id = %s", (id, id, id))

        if group_fights:
            return [GroupFight(group_fight[0], group_fight[1], group_fight[2], group_fight[3], group_fight[4], group_fight[5]) for group_fight in group_fights]
        else:
            return None
            
    def throws(id):
        class Throw:
            def __init__(self, id, thrower_id, target_id, success, chocolate_egg_bet):
                self.id = id
                self.thrower_id = thrower_id
                self.target_id = target_id
                self.success = True if success == 1 else False
                self.chocolate_egg_bet = chocolate_egg_bet
        throws = Database.execute_and_fetchall("SELECT * FROM throws WHERE user_id = %s", (id,))
        if throws:
            return [Throw(throw[0], throw[1], throw[2], throw[3], throw[4]) for throw in throws]
        else:
            return None
        
    def hits(id):
        throws = 0
        hits = 0
        for throw in Get.throws(id):
            if throw.target_id == id:
                throws += 1
                if throw.success:
                    hits += 1
        
        if hits:
            return (throws, hits)
        else:
            return None
        
    def own_throws(id):
        throws = Get.throws(id)
        if throws:
            return [throw for throw in throws if throw.thrower_id == id]
        else:
            return None
        
    def cakes(id):
        class Cake:
            def __init__(self, id, user_id):
                self.id = id
                self.user_id = user_id
        cakes = Database.execute_and_fetchall("SELECT * FROM cakes WHERE user_id = %s", (id,))
        if cakes:
            return [Cake(cake[0], cake[1]) for cake in cakes]
        else:
            return None
    
class Add:
    def user(id):
        Database.execute_and_commit("INSERT INTO users (user_id, last_hit, egg_talisman, rabbit_foot_count, used_rabbit_foot_count) VALUES (%s, %s, %s, %s, %s)", (id, 0, 0, 0, 0))
        
    def egg(id, type):
        Database.execute_and_commit("INSERT INTO eggs (owner_id, creator_id, type, is_rotten) VALUES (%s, %s, %s, %s)", (id, id, type, 0))
        
    def solo_fight(challenger_id, defender_id, chocolate_egg_bet, winner_id):
        Database.execute_and_commit("INSERT INTO egg_fights (challenger_id, defender_id, chocolate_egg_bet, winner_id) VALUES (%s, %s, %s, %s)", (challenger_id, defender_id, chocolate_egg_bet, winner_id))
        
    def group_fight(participants, chocolate_egg_bet, first_place_id, second_place_id, third_place_id):
        Database.execute_and_commit("INSERT INTO group_fights (participants, chocolate_egg_bet, first_place_id, second_place_id, third_place_id) VALUES (%s, %s, %s, %s, %s)", (len(participants), chocolate_egg_bet, first_place_id, second_place_id, third_place_id))
        
    def throw(thrower_id, target_id, success, chocolate_egg_bet):
        Database.execute_and_commit("INSERT INTO throws (thrower_id, target_id, success, chocolate_egg_bet) VALUES (%s, %s, %s, %s)", (thrower_id, target_id, success, chocolate_egg_bet))
        
    def cake(user_id):
        Database.execute_and_commit("INSERT INTO cakes (user_id) VALUES (%s)", (user_id,))

class Update:
    def user_last_hit(id):
        Database.execute_and_commit("UPDATE users SET last_hit = %s WHERE user_id = %s", (tm.time(), id))

    def user_egg_talisman(id, egg_talisman):
        Database.execute_and_commit("UPDATE users SET egg_talisman = %s WHERE user_id = %s", (egg_talisman, id))

    def user_add_one_rabbit_foot_count(id):
        Database.execute_and_commit("UPDATE users SET rabbit_foot_count = rabbit_foot_count + 1 WHERE user_id = %s", (id,))

    def user_remove_one_rabbit_foot_count(id):
        Database.execute_and_commit("UPDATE users SET rabbit_foot_count = rabbit_foot_count - 1, used_rabbit_foot_count = used_rabbit_foot_count - 1 WHERE user_id = %s", (id,))

    def egg_owner(id, owner_id):
        Database.execute_and_commit("UPDATE eggs SET owner_id = %s WHERE egg_id = %s", (owner_id, id))


class Gen:
    def nest(location, type=0, schokoei=0, gekochtesEi=0, ungekochtesEi=0, egg_talisman=0, rabbit_foot_count=0):
        class Nest:
            def __init__(self, location, type, schokoei, gekochtesEi, ungekochtesEi, egg_talisman, rabbit_foot_count):
                self.location = location
                self.type = type
                self.schokoei = schokoei
                self.gekochtesEi = gekochtesEi
                self.ungekochtesEi = ungekochtesEi
                self.egg_talisman = egg_talisman
                self.rabbit_foot_count = rabbit_foot_count
        return Nest(location, type, schokoei, gekochtesEi, ungekochtesEi, egg_talisman, rabbit_foot_count)


class Translate:
    def nest(nest):
        if nest.type == "empty":
            return "Nest leer"
        else:
            nest_info = ""
            if nest.schokoei != 0:
                nest_info += f"Schokoeier: {nest.schokoei}\n"
            if nest.gekochtesEi != 0:
                nest_info += f"Gekochte Eier: {nest.gekochtesEi}\n"
            if nest.ungekochtesEi != 0:
                nest_info += f"Ungekochte Eier: {nest.ungekochtesEi}\n"
            if nest.egg_talisman != 0:
                nest_info += f"Eier-Talisman\n"
            if nest.rabbit_foot_count != 0:
                nest_info += f"Hasenpfote\n"
            return nest_info.strip()