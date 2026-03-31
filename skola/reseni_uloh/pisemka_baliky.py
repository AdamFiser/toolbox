baliky = ["B541X", "B547X","B251X", "B501X", "B947X"]

baliky.append("AB55X")

for balik in baliky:
    print("text", balik)

n = None
p = 0
while n != 0:
    n = int(input("Zadej vstup: "))
    p += 1
else:
    print("Konec zadavani, pocet pokusu:", p)

den = int(input("Zadej den: "))
if den >= 1 and den <= 5:
    print("Pracovní den")
elif den == 6 or den == 7:
    print("Víkend")
elif den == 0:
    print("svátek")
else:
    print("neplatný vsutp")

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
    ]

pocet = 0
populace = 0
for stat in staty:
    pocet += 1

    if stat["region"] == "Europe":
        populace += stat["population"]
    elif stat["region"] == "Polar":
        print(stat["population"])
