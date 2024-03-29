import system

import random

data = system.Database.execute_and_fetchall("SELECT * FROM users")

users = [user[0] for user in data]
print(len(users))

for i in range(3):
    print(random.choice(users))

#435110642211618829
#199875305102508032