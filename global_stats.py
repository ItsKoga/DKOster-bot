import system
import time

start = time.time()

users = system.Database.execute_and_fetchall("SELECT * FROM users")
for user in users:
    if user[0] == "111111111111111111":
        users.remove(user)
print(f"Users Gesamt: {len(users)}")
amount_0 = 0
for user in users:
    amount_0 += system.Get.points(user[0])
print(f"Punkte insgesamt: {amount_0}")

users_with_talisman = [user for user in users if user[2] != 0]
print(f"User mit Talisman: {len(users_with_talisman)}")

current_rabbit_foots = [user for user in users if user[3] != 0]
amount_1 = 0
for user in current_rabbit_foots:
    amount_1 += user[3]

print(f"Aktuelle Hasenpfoten: {amount_1}")

used_rabbit_foots = [user for user in users if user[4] != 0]
amount_2 = 0
for user in used_rabbit_foots:
    amount_2 += user[4]
print(f"Benutzte Hasenpfoten: {amount_2}")

print(f"Hasenpfoten insgesamt: {amount_1 + amount_2}")

used_collects = [user for user in users if user[8] != 0]
amount_3 = 0
for user in used_collects:
    amount_3 += user[8]
print(f"/collect ausgeführt: {amount_3}")

found_nests = [user for user in users if user[9] != 0]
amount_4 = 0
for user in found_nests:
    amount_4 += user[9]
print(f"Nester gefunden(nicht leer): {amount_4}")

print("\n")

print("Top 5 User, die am meisten /collect ausgeführt haben:")
users.sort(key=lambda x: x[8], reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users[i][0]}> : {users[i][8]}")

class User:
    def __init__(self, user_id, cakes):
        self.user_id = user_id
        self.cakes = cakes

users_created_cakes = []
for user in users:
    cakes = system.Database.execute_and_fetchall(f"SELECT * FROM cakes WHERE user_id = '{user[0]}'")
    users_created_cakes.append(User(user[0], cakes))

print("**Top 5 User, die die meisten Kuchen erstellt haben:**")
users_created_cakes.sort(key=lambda x: len(x.cakes), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users_created_cakes[i].user_id}> : {len(users_created_cakes[i].cakes)} Kuchen")


print("\n")

eggs = system.Database.execute_and_fetchall("SELECT * FROM eggs")
cakes = system.Database.execute_and_fetchall("SELECT * FROM cakes")
print(f"Kuchen insgesamt: {len(cakes)}")

chocolate_eggs = [egg for egg in eggs if egg[3] == "Schokoei"]
amount_5 = len(chocolate_eggs) + len(cakes)*10
print(f"Schokoeier insgesamt gefunden: {amount_5}")

cooked_eggs = [egg for egg in eggs if egg[3] == "gekochtes Hühnerei"]
deleted_cooked = system.Database.execute_and_fetchall("SELECT * FROM stats WHERE stat = 'deleted_cooked'")[0][1]
amount_6 = len(cooked_eggs) + deleted_cooked
print(f"Gekochte Eier insgesamt gefunden: {amount_6}")

uncooked_eggs = [egg for egg in eggs if egg[3] == "ungekochtes Hühnerei"]
deleted_uncooked = system.Database.execute_and_fetchall("SELECT * FROM stats WHERE stat = 'deleted_uncooked'")[0][1]
amount_7 = len(uncooked_eggs) + deleted_uncooked
print(f"Ungekochte Eier insgesamt gefunden: {amount_7}")

print("\n")

users_created_eggs = []
class User:
    def __init__(self, user_id, chocolate_eggs, cooked_eggs, uncooked_eggs):
        self.user_id = user_id
        self.chocolate_eggs = chocolate_eggs
        self.cooked_eggs = cooked_eggs
        self.uncooked_eggs = uncooked_eggs
for user in users:
    chocolate_eggs = [egg for egg in eggs if egg[3] == "Schokoei" and egg[1] == user[0]]
    cooked_eggs = [egg for egg in eggs if egg[3] == "gekochtes Hühnerei" and egg[1] == user[0]]
    uncooked_eggs = [egg for egg in eggs if egg[3] == "ungekochtes Hühnerei" and egg[1] == user[0]]

    users_created_eggs.append(User(user[0], chocolate_eggs, cooked_eggs, uncooked_eggs))

print("**Top 5 User, die die meisten Schokoeier erstellt haben:**")
users_created_eggs.sort(key=lambda x: len(x.chocolate_eggs), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users_created_eggs[i].user_id}> : {len(users_created_eggs[i].chocolate_eggs)} Schokoeier")
 
print("**Top 5 User, die die meisten gekochten Eier erstellt haben:**")
users_created_eggs.sort(key=lambda x: len(x.cooked_eggs), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users_created_eggs[i].user_id}> : {len(users_created_eggs[i].cooked_eggs)} gekochte Eier")

print("**Top 5 User, die die meisten ungekochten Eier erstellt haben:**")
users_created_eggs.sort(key=lambda x: len(x.uncooked_eggs), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users_created_eggs[i].user_id}> : {len(users_created_eggs[i].uncooked_eggs)} ungekochte Eier")

print("**Top 5 User, die die meisten Eier erstellt haben:**")
users_created_eggs.sort(key=lambda x: len(x.chocolate_eggs) + len(x.cooked_eggs) + len(x.uncooked_eggs), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{users_created_eggs[i].user_id}> : {len(users_created_eggs[i].chocolate_eggs) + len(users_created_eggs[i].cooked_eggs) + len(users_created_eggs[i].uncooked_eggs)} Eier")

print("\n")

solo_fights = system.Database.execute_and_fetchall("SELECT * FROM egg_fights")
print(f"Kämpfe insgesamt: {len(solo_fights)}")

print("\n")

class User:
    def __init__(self, user_id, fights, wins, losses, started, accepted):
        self.user_id = user_id
        self.fights = fights
        self.wins = wins
        self.losses = losses
        self.started = started
        self.accepted = accepted

fights = []
for user in users:
    fights_list = [fight for fight in solo_fights if fight[1] == user[0] or fight[2] == user[0]]
    wins = [fight for fight in fights_list if fight[4] == user[0]]
    losses = [fight for fight in fights_list if fight[4] != user[0]]
    started = [fight for fight in fights_list if fight[1] == user[0]]
    accepted = [fight for fight in fights_list if fight[2] == user[0]]

    fights.append(User(user[0], fights_list, wins, losses, started, accepted))

print("**Top 5 User, die die meisten Solo-Fights gewonnen haben:**")
fights.sort(key=lambda x: len(x.wins), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{fights[i].user_id}> : {len(fights[i].wins)} Siege")

print("**Top 5 User, die die meisten Solo-Fights verloren haben:**")
fights.sort(key=lambda x: len(x.losses), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{fights[i].user_id}> : {len(fights[i].losses)} Niederlagen")

print("**Top 5 User, die die meisten Solo-Fights gestartet haben:**")
fights.sort(key=lambda x: len(x.started), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{fights[i].user_id}> : {len(fights[i].started)} Kämpfe gestartet")

print("**Top 5 User, die die meisten Solo-Fight Anfragen angenommen haben:**")
fights.sort(key=lambda x: len(x.accepted), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{fights[i].user_id}> : {len(fights[i].accepted)} Anfragen angenommen")

print("\n")

throws = system.Database.execute_and_fetchall("SELECT * FROM egg_throws")
print(f"Würfe insgesamt: {len(throws)}")

print("\n")

class User:
    def __init__(self, user_id, throws):
        self.user_id = user_id
        self.throws = [throw for throw in throws if throw[1] == user_id]
        self.successful_throws = [throw for throw in throws if throw[1] == user_id and throw[3] == 1]
        self.hits = [throw for throw in throws if throw[2] == user_id and throw[3] == 1]
        self.hits_received = [throw for throw in throws if throw[2] == user_id]

throws_list = []
for user in users:
    throws_list.append(User(user[0], [throw for throw in throws if throw[1] == user[0] or throw[2] == user[0]]))

print("**Top 5 User, die die meisten Eier geworfen haben:**")
throws_list.sort(key=lambda x: len(x.throws), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{throws_list[i].user_id}> : {len(throws_list[i].throws)} Würfe")

print("**Top 5 User, die die meisten erfolgreichen Eierwürfe hatten:**")
throws_list.sort(key=lambda x: len(x.successful_throws), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{throws_list[i].user_id}> : {len(throws_list[i].successful_throws)} erfolgreiche Würfe")

print("**Top 5 User, die am meisten abgeworfen wurden:**")
throws_list.sort(key=lambda x: len(x.hits_received), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{throws_list[i].user_id}> : {len(throws_list[i].hits_received)} Versuche")

print("**Top 5 User, die am meisten von Eiern getroffen worden:**")
throws_list.sort(key=lambda x: len(x.hits), reverse=True)
for i in range(5):
    print(f"{i + 1}. <@{throws_list[i].user_id}> : {len(throws_list[i].hits)}x getroffen worden")

print("\n")

for location in ["1", "2", "3", "4", "5"]:
    data = system.Database.execute_and_fetchall(f"SELECT * FROM stats WHERE stat = '{location}'")
    print(f"An der Location {location} wurde {data[0][1]} mal gesucht")



print(f"\nTime: {time.strftime('%M:%S', time.gmtime(time.time() - start))}")