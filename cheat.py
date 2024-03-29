import system


id = 499198101383282689

for i in range(10):
    print(i)
    system.Add.egg(id, "Schokoei")
system.Add.egg(id, "gekochtes Hühnerei")
system.Add.egg(id, "ungekochtes Hühnerei")

system.Get.points(id)