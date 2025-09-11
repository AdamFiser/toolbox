import requests
from bs4 import BeautifulSoup
import os

url = "https://www.zsr.sk/dopravcovia/infrastruktura/tabulky-tratovych-pomerov/"
resp = requests.get(url)
soup = BeautifulSoup(resp.text, "html.parser")

links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if href.lower().endswith('.pdf'):
        full = href if href.startswith('http') else 'https://www.zsr.sk' + href
        links.append(full)

os.makedirs('SK_TTP', exist_ok=True)
for link in links:
    fname = os.path.join('SK_TTP', link.split('/')[-1])
    r = requests.get(link)
    with open(fname, 'wb') as f:
        f.write(r.content)
    print("Stahnute:", fname)
