rady = ["Eanos", "Eas", "Falls", "Zagz", "Sggrss"]

rady.append("Eacs")

for rada in rady:
    print("Řada: ", rada)

vstup = None
pocet = 0
while vstup != "stop":
    vstup = input("Zadej číslo (pro ukočení napiš 'stop'): ")
    pocet += 1
else:
    print("Počet vstupů:", pocet)

mesic = int(input("Zadej měsíc (1-12): "))
if 1 <= mesic <= 3:
    print("Jaro")
elif mesic >= 4 and mesic <= 6:
    print("Léto")
else:
    print("nepodporovaný vstup")

staty = [
    {'name': 'Afghanistan', 'capital': 'Kabul', 'region': 'Asia', 'subregion': 'Southern Asia', 'population': 27657145, 'area': 652230.0, 'gini': 27.8},
    {'name': 'Åland Islands', 'capital': 'Mariehamn', 'region': 'Europe', 'subregion': 'Northern Europe', 'population': 28875, 'area': 1580.0},
    {'name': 'Albania', 'capital': 'Tirana', 'region': 'Europe', 'subregion': 'Southern Europe', 'population': 2886026, 'area': 28748.0, 'gini': 34.5},
    {'name': 'Algeria', 'capital': 'Algiers', 'region': 'Africa', 'subregion': 'Northern Africa', 'population': 40400000, 'area': 2381741.0, 'gini': 35.3},
    {'name': 'American Samoa', 'capital': 'Pago Pago', 'region': 'Oceania', 'subregion': 'Polynesia', 'population': 57100, 'area': 199.0},
    {'name': 'Andorra', 'capital': 'Andorra la Vella', 'region': 'Europe', 'subregion': 'Southern Europe', 'population': 78014, 'area': 468.0},
    {'name': 'Angola', 'capital': 'Luanda', 'region': 'Africa', 'subregion': 'Middle Africa', 'population': 25868000, 'area': 1246700.0, 'gini': 58.6},
    {'name': 'Anguilla', 'capital': 'The Valley', 'region': 'Americas', 'subregion': 'Caribbean', 'population': 13452, 'area': 91.0},
    {'name': 'Antarctica', 'capital': '', 'region': 'Polar', 'subregion': '', 'population': 1000, 'area': 14000000.0},
    {'name': 'Antigua and Barbuda', 'capital': "Saint John's", 'region': 'Americas', 'subregion': 'Caribbean', 'population': 86295, 'area': 442.0}
    {'name': 'Bahamas', 'capital': 'Nassau', 'region': 'Americas', 'subregion': 'Caribbean', 'population': 378040, 'area': 13943.0},
    {'name': 'Bahrain', 'capital': 'Manama', 'region': 'Asia', 'subregion': 'Western Asia', 'population': 1404900,'area': 765.0},
    ]

pocet = 0
rozloha = 0
for stat in staty:
    pocet += 1
    #print(stat["name"])

    if stat["region"] == "Europe":
        rozloha += stat["area"]
    if stat["region"] == "Oceania":
        print(stat["name"])