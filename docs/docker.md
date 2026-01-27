# Docker

## Instalace nového containeru
1. `cd /opt`
2. `git clone https://github.com/AdamFiser/projekt.git`
   1. alternativně pro specifickou verzi `git clone --branch beta-1.1.0 --depth 1 https://github.com/AdamFiser/projekt.git`
2. `sudo chown -R afiser:afiser /opt/projekt`
3. `cd projekt`
4. upravit soubor `docker-compose.yml`
5. `docker compose build`
6. `docker compose up -d`


## Odstranění

1. `cd /opt/projekt`
2. `docker compose down -v`
3. `cd ..`
4. `rm -rf projekt`


## Logování

1. `docker compose ps`
2. `docker compose logs --tail=200`