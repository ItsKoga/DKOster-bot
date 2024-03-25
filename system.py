import os

import time as tm
import random

import mysql.connector
from mysql.connector import Error

class Database:

    def connect():
        class Connection:
            def __init__(self):
                self.connection = None
                self.cursor = None
                self.connected = False
                self.enter()

            def enter(self):
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

            def close(self):
                if self.connected:
                    self.connection.commit()
                    self.cursor.close()
                    self.connection.close()
                    self.connected = False

        return Connection()
    
    def execute_and_fetchall(query, values=None):
        connection = Database.connect()
        if connection.connected:
            if values:
                connection.cursor.execute(query, values)
            else:
                connection.cursor.execute(query)
            data = connection.cursor.fetchall()
        else:
            data = None
        connection.close()
        return data
        
            
    def execute_and_commit(query, values=None):
        connection = Database.connect()
        if connection.connected:
            if values:
                connection.cursor.execute(query, values)
            else:
                connection.cursor.execute(query)
            connection.connection.commit()
        connection.close()
            
    def execute_and_fetchone(query, values=None):
        connection = Database.connect()
        if connection.connected:
            if values:
                connection.cursor.execute(query, values)
            else:
                connection.cursor.execute(query)
            data = connection.cursor.fetchone()
        else:
            data = None
        connection.close()
        return data
            

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
        
    def probabilities(id):
        profile = Get.user(id)
        cooked = 0.8 if profile.egg_talisman == 0 else 0.9 if profile.egg_talisman == 1 else 0.7
        uncooked = round(1 - cooked, 1)
        return (cooked, uncooked)
        
    def points(id):
        chocolate_eggs = len(Get.type_eggs(id, "Schokoei"))

        cakes = Get.cakes(id)
        points = chocolate_eggs + len(cakes) * 10

        Database.execute_and_commit("UPDATE users SET points = %s WHERE user_id = %s", (points, id))
        return points
    
    
    def eggs(id):
        class Egg:
            def __init__(self, id, owner_id, creator_id, type, is_rotten, time):
                self.id = id
                self.owner_id = owner_id
                self.creator_id = creator_id
                self.type = type
                self.is_rotten = True if ((is_rotten <= time-3600 and type == "ungekochtes Hühnerei") or (is_rotten <= time-28800 and type == "gekochtes Hühnerei")) else False
        eggs = Database.execute_and_fetchall("SELECT * FROM eggs WHERE owner_id = %s", (id,))
        time = tm.time()
        if eggs:
            return [Egg(egg[0], egg[1], egg[2], egg[3], egg[4], time) for egg in eggs]
        else:
            return []
        
    def type_eggs(id, type):
        class Egg:
            def __init__(self, id, owner_id, creator_id, type, is_rotten, time):
                self.id = id
                self.owner_id = owner_id
                self.creator_id = creator_id
                self.type = type
                self.is_rotten = True if ((is_rotten <= time-3600 and type == "ungekochtes Hühnerei") or (is_rotten <= time-28800 and type == "gekochtes Hühnerei")) else False
        eggs = Database.execute_and_fetchall("SELECT * FROM eggs WHERE owner_id = %s AND type = %s", (id, type))
        time = tm.time()
        if eggs:
            return [Egg(egg[0], egg[1], egg[2], egg[3], egg[4], time) for egg in eggs]
        else:
            return []
        
    def egg(id):
        class Egg:
            def __init__(self, id, owner_id, creator_id, type, is_rotten, time):
                self.id = id
                self.owner_id = owner_id
                self.creator_id = creator_id
                self.type = type
                self.is_rotten = True if ((is_rotten <= time-3600 and type == "ungekochtes Hühnerei") or (is_rotten <= time-28800 and type == "gekochtes Hühnerei")) else False
        egg = Database.execute_and_fetchone("SELECT * FROM eggs WHERE owner_id = %s", (id,))
        time = tm.time()
        if egg:
            return Egg(egg[0], egg[1], egg[2], egg[3], egg[4], time)
        else:
            return None
        
    def egg_check(id, type):
        eggs = Get.eggs(id)
        for egg in eggs:
            if egg.type == type and egg.is_rotten == False:
                return egg
        return False
    
    def bake_check(id):
        eggs = Get.eggs(id)
        chocolate_eggs = 0
        uncooked_eggs = 0
        for egg in eggs:
            if egg.type == "Schokoei":
                chocolate_eggs += 1
            elif egg.type == "ungekochtes Hühnerei":
                uncooked_eggs += 1
        if chocolate_eggs >= 10 and uncooked_eggs >= 3:
            return True
        else:
            return False
        
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
            def __init__(self, id, thrower_id, target_id, success):
                self.id = id
                self.thrower_id = thrower_id
                self.target_id = target_id
                self.success = True if success == 1 else False
        throws = Database.execute_and_fetchall("SELECT * FROM egg_throws WHERE thrower_id = %s OR target_id = %s", (id, id,))
        if throws:
            return [Throw(throw[0], throw[1], throw[2], throw[3]) for throw in throws]
        else:
            return None
        
    def hits(id):
        throws = 0
        hits = 0
        data = Get.throws(id)
        if not data:
            return (0, 0)
        for throw in data:
            if throw.target_id == str(id):
                throws += 1
                if throw.success:
                    hits += 1
        
        return (throws, hits)
        
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
            return []
        
    def notifications(id):
        notifications = Database.execute_and_fetchall("SELECT notifications FROM users WHERE user_id = %s", (id,))
        return True if notifications[0][0] == 1 else False
    
    def top(limit):
        class User:
            def __init__(self, id, points):
                self.id = id
                self.points = points
        users = Database.execute_and_fetchall("SELECT user_id, points FROM users ORDER BY points DESC LIMIT %s", (limit,))
        if users:
            return [User(user[0], user[1]) for user in users]
        else:
            return None
        
    def top_position(id):
        users = Get.top(1000)
        for i, user in enumerate(users):
            if user.id == str(id):
                return i+1
        return None
    
    
class Add:
    def user(id):
        Database.execute_and_commit("INSERT INTO users (user_id, last_hit, egg_talisman, rabbit_foot_count, used_rabbit_foot_count) VALUES (%s, %s, %s, %s, %s)", (id, 0, 0, 0, 0))
        
    def egg(id, type):
        Database.execute_and_commit("INSERT INTO eggs (owner_id, creator_id, type, is_rotten) VALUES (%s, %s, %s, %s)", (id, id, type, tm.time()))
        
    def solo_fight(challenger_id, defender_id, chocolate_egg_bet, winner_id):
        Database.execute_and_commit("INSERT INTO egg_fights (challenger_id, defender_id, chocolate_egg_bet, winner_id) VALUES (%s, %s, %s, %s)", (challenger_id, defender_id, chocolate_egg_bet, winner_id))
        
    def group_fight(participants, chocolate_egg_bet, first_place_id, second_place_id, third_place_id):
        Database.execute_and_commit("INSERT INTO group_fights (participants, chocolate_egg_bet, first_place_id, second_place_id, third_place_id) VALUES (%s, %s, %s, %s, %s)", (len(participants), chocolate_egg_bet, first_place_id, second_place_id, third_place_id))
        
    def throw(thrower_id, target_id, success):
        Database.execute_and_commit("INSERT INTO egg_throws (thrower_id, target_id, success) VALUES (%s, %s, %s)", (thrower_id, target_id, success))
        
    def cake(user_id):
        Database.execute_and_commit("INSERT INTO cakes (user_id) VALUES (%s)", (user_id,))
        #remove 10 chocolate eggs and 3 uncooked eggs
        eggs = Get.type_eggs(user_id, "Schokoei")
        for i in range(10):
            Delete.egg(eggs[i].id)
        eggs = Get.type_eggs(user_id, "ungekochtes Hühnerei")
        for i in range(3):
            Delete.egg(eggs[i].id)

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

    def user_notifications(id, notifications):
        Database.execute_and_commit("UPDATE users SET notifications = %s WHERE user_id = %s", (notifications, id))

    def leaderboard(limit):
        users = Get.top(limit)
        for i, user in enumerate(users):
            points = Get.points(user.id)
            Database.execute_and_commit("UPDATE users SET points = %s WHERE user_id = %s", (points, user.id))

        return True
            


class Gen:
    def nest(location, ctx):
        class Nest:
            def __init__(self, location, type, schokoei=0, gekochtesEi=0, ungekochtesEi=0, egg_talisman=0, rabbit_foot_count=0):
                self.location = location
                self.type = type
                self.schokoei = schokoei
                self.gekochtesEi = gekochtesEi
                self.ungekochtesEi = ungekochtesEi
                self.egg_talisman = egg_talisman
                self.rabbit_foot_count = rabbit_foot_count

        probabilities = Get.probabilities(ctx.author.id)
        type = random.choices(["empty", "normal", "special"], weights=[0.5, 0.4, 0.1])[0]
        if type == "empty":
            return Nest(location=location, type="empty")
        elif type == "normal":
            return Nest(location=location, type="normal",
                                                   schokoei=random.randint(1, 10),
                                                   gekochtesEi=0 if random.random() < probabilities[0] else random.randint(1, 2),
                                                   ungekochtesEi=0 if random.random() < probabilities[1] else random.randint(1, 2))
        elif type == "special":
            return Nest(location=location, type="special",
                                                   schokoei=random.randint(1, 10),
                                                   gekochtesEi=random.randint(1, 2) if random.random() <= 0.9 else 0,
                                                   ungekochtesEi=random.randint(1, 2) if random.random() <= 0.1 else 0,
                                                   egg_talisman=1 if Get.user(ctx.author.id).egg_talisman or random.random() <= 0.1 else 0,
                                                   rabbit_foot_count=1 if random.random() <= 0.25 else 0)


class Translate:
    def nest(nest):
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
                nest_info += f"Hasenpfote\n"
            return nest_info.strip()
        

    def leaderboard(top):
        string = ""
        top = Get.top(top)
        for i, user in enumerate(top):
            string += f"{i+1}. <@{user.id}> - {user.points}\n"
        
        return string.strip()

        
class Delete:
    def egg(id):
        Database.execute_and_commit("DELETE FROM eggs WHERE egg_id = %s", (id,))