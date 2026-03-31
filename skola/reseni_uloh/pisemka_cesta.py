from datetime import date, timedelta

dnes = date.today()
print(dnes.strftime("%A %d. %m. %y"))

date(dnes.year, dnes.month, 1)

if (dnes.month == 12):
    pom = date(dnes.year + 1, 1, 1)
else
    pom = date((dnes.year, dnes.month, 1)

    poslednien = pom - timedlta(days=1)


def getConsumption(phm: str) -> float:
    rate = {
        "nafta": 35,
        "benzin": 30
    }

    try:
        vysledek = rate[phm.lower()]
    except:
        raise ValueError("neplatný parametr")

    return vysledek


getConsumption("Nafta")


def getCosts(km: int, phm: str = "nafta"):
    cena = getConsumption(phm)

    naklad = (cena * km) / 100

    return naklad


trasa = 100
print("Náklady pro trasu ", trasa, "jsou ", getCosts(trasa, "nafta"))
getCosts(trasa, "benzin")
getCosts(trasa, "elektro")