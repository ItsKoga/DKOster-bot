import random


amount = 100000 # Amount of /collects to simulate

chocolate_eggs = 0
cooked_eggs = 0
uncooked_eggs = 0
rabbit_foots = 0
talisman = 0

empty = 0
normal = 0
special = 0


class Gen:
    def nest(location, rabbit_foot=False):
        class Nest:
            def __init__(self, location, type, schokoei=0, gekochtesEi=0, ungekochtesEi=0, egg_talisman=0, rabbit_foot_count=0):
                self.location = location
                self.type = type
                self.schokoei = schokoei
                self.gekochtesEi = gekochtesEi
                self.ungekochtesEi = ungekochtesEi
                self.egg_talisman = egg_talisman
                self.rabbit_foot_count = rabbit_foot_count

        probabilities = (0.577, 0.296)# 1: gekochtes Ei, 2: ungekochtes Ei
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
                                                   egg_talisman=1 if True and random.random() <= 0.27 else 0,
                                                   rabbit_foot_count=1 * (2 if rabbit_foot else 1) if random.random() <= 0.395 else 0)

for i in range(amount):
    locations = ["1", "2", "3", "4", "5"]
    nests = []
    for j in range(5):
        nests.append(Gen.nest(locations[j]))

    choice = random.choice(nests)


    chocolate_eggs += choice.schokoei
    cooked_eggs += choice.gekochtesEi
    uncooked_eggs += choice.ungekochtesEi
    rabbit_foots += choice.rabbit_foot_count
    talisman += choice.egg_talisman

    if choice.type == "empty":
        empty += 1
    elif choice.type == "normal":
        normal += 1
    elif choice.type == "special":
        special += 1

    print(f"Collect {i+1} done")

def print_better(amountOf, name):
    print(f"{name}: {amountOf}{' '*(20-len(name)-len(str(amountOf)))}Pro /collect: {amountOf/amount}{' '*(20-len(str(round(amountOf/amount, 2))))}1 pro {round(amount/amountOf, 2)} /collects")

print_better(chocolate_eggs, "Schokoeier")
print_better(cooked_eggs, "Gekochte Eier")
print_better(uncooked_eggs, "Ungekochte Eier")
print_better(rabbit_foots, "Hasenpfoten")
print_better(talisman, "Talisman")
print_better(empty, "Leere Nester")
print_better(normal, "Normale Nester")
print_better(special, "Spezielle Nester")

cakes = 0
for i in range(chocolate_eggs//10):
    if chocolate_eggs >= 10 and uncooked_eggs >= 3:
        cakes += 1
        chocolate_eggs -= 10
        uncooked_eggs -= 3

print(f"Kuchen insgesamt: {cakes}")
print(f"Restliche Schokoeier: {chocolate_eggs}")
print(f"Restliche Ungekochte Eier: {uncooked_eggs}")

points = chocolate_eggs + cakes*10
print(f"Prozentualer Anteil der Kuchen an den Punkten: {round(cakes*10/points*100, 2)}%")

    