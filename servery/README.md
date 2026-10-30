# Servery

Dokumentace a nástroje pro správu docker serverů PKPCI.

## Inventář

| Server | OS | Přístup | Portainer |
|---|---|---|---|
| `docker.pkpcargointernational.com` (hostname `czmugdocker`) | CentOS Stream 9, Docker 29 | `ssh afiser@…` (skupina `docker`, bez sudo) | **server** `portainer/portainer-ce:lts`, porty 8000 (edge tunel) a 9443 (UI), data ve volume `portainer_data` |
| `bestie.pkpcargointernational.com` (`10.136.34.199`) | Ubuntu 24.04, Docker 29 | `ssh aiops@…` (skupina `docker`) | **agent** `portainer/agent`, kontejner `portainer_agent`, port 9001 |

V Portaineru jsou zaregistrovaná dvě prostředí: lokální socket serveru `docker`
a `tcp://bestie.pkpcargointernational.com:9001` (agent).

## SSH přístup

Nástroje používají klíč `~/.ssh/id_ed25519_toolbox` (cesta jde změnit
proměnnou `SSH_KEY`). Veřejný klíč je v `~/.ssh/authorized_keys` uživatele
na každém serveru. Postup přidání nového serveru:

```bash
ssh-copy-id -i ~/.ssh/id_ed25519_toolbox.pub uzivatel@server   # zeptá se na heslo
```

Původní klíč účtu `aiops` na bestii je v Bitwarden Secrets Manageru
(`bitwarden.pkpcargointernational.com`) jako secret `BESTIE_SSH_PRIVATE_KEY_B64`
(soukromý klíč v base64). Načtení přes [`bws`](https://github.com/bitwarden/sdk-sm):

```bash
export BWS_ACCESS_TOKEN=$(cat ~/.config/bws/token)
bws secret list --server-url https://bitwarden.pkpcargointernational.com
bws secret get <id> --server-url https://bitwarden.pkpcargointernational.com -o json \
	| python -c "import sys,json,base64;sys.stdout.buffer.write(base64.b64decode(json.load(sys.stdin)['value']))" > ~/.ssh/id_bestie
```

## Aktualizace Portaineru

```bash
servery/portainer/update-portainer.sh          # server i agenti
servery/portainer/update-portainer.sh server   # jen server
servery/portainer/update-portainer.sh agents   # jen agenti
```

Spouštěj z Git Bash. Postup skriptu:

1. **Server** (`docker`): stáhne `portainer/portainer-ce:lts`. Když image
   odpovídá běžícímu kontejneru, nic nedělá. Jinak kontejner zastaví,
   zazálohuje volume `portainer_data` do `~/backups/portainer/` na serveru
   a vytvoří kontejner znovu se stejnými parametry.
2. **Agenti**: zjistí verzi serveru z `https://docker.pkpcargointernational.com:9443/api/system/status`
   a na každém hostu z `AGENT_HOSTS` stejně vymění kontejner `portainer_agent`
   za `portainer/agent:<verze serveru>`. Agent musí mít stejnou verzi jako server.
   Portainer UI přebírá verzi agenta až z pravidelného snapshotu prostředí
   (`SnapshotInterval`, výchozí 5 min). Do té doby ukazuje starou verzi.

Výměnu kontejneru dělá `portainer/recreate-container.sh`. Ten běží na serveru:
starý kontejner přejmenuje na `<název>-old` a nový ověří po 10 s. Když nový
neběží, smaže ho a vrátí původní kontejner.

### Agent bez `AGENT_SECRET`

Agent na bestii běží bez `AGENT_SECRET`, stejně jako před aktualizací. Bez
sdíleného secretu agent přijme první Portainer server, který se k němu připojí,
a to i po každém novém vytvoření kontejneru. Port 9001 je proto vhodné omezit
firewallem jen na `docker.pkpcargointernational.com`, nebo nastavit stejný
`AGENT_SECRET` na serveru i na všech agentech.

### Obnova ze zálohy

```bash
docker stop portainer
docker run --rm -v portainer_data:/data -v ~/backups/portainer:/backup alpine \
	sh -c 'rm -rf /data/* && tar xzf /backup/portainer_data-<datum>.tar.gz -C /data'
docker start portainer
```

Starší verze Portaineru nemusí přečíst databázi migrovanou novější verzí.
Při návratu na starší verzi proto obnov i zálohu z doby před aktualizací.

## Aktualizace Bitwardenu

Na `docker` běží oficiální self-hosted Bitwarden (standardní instalace přes
`bitwarden.sh`, 11 kontejnerů `bitwarden-*`) v `/opt/bitwarden`. Adresář patří
uživateli `bitwarden` s právy `700`. `afiser` do něj nevidí a `sudo` bez hesla
nemá, takže aktualizaci spouští člověk přihlášený přímo jako `bitwarden`
(heslem). `bitwarden` není v sudoers, `sudo -iu bitwarden` proto nepoužívej.

Databáze se jmenuje `pkpci_vault`, ne `vault` jako v příkladech v dokumentaci.
Nginx publikuje porty `6443` (HTTPS) a `8280` (HTTP).

Postup vychází z oficiální dokumentace:
[Update](https://bitwarden.com/help/updating-on-premise/),
[Backup](https://bitwarden.com/help/backup-on-premise/),
[příkazy `bitwarden.sh`](https://bitwarden.com/help/install-on-premise-linux/).
Změny mezi verzemi jsou v [release notes](https://github.com/bitwarden/self-host/releases).

### 1. Záloha databáze (jako `afiser`, bez výpadku)

```bash
docker exec -i bitwarden-mssql /backup-db.sh
docker exec bitwarden-mssql ls -lt /etc/bitwarden/mssql/backups | head -3
```

Ověření integrity zálohy. Heslo `sa` se bere z proměnné `SA_PASSWORD`
v kontejneru, nikde se nevypisuje:

```bash
docker exec bitwarden-mssql bash -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C \
	-Q "RESTORE VERIFYONLY FROM DISK = '"'"'/etc/bitwarden/mssql/backups/<soubor>.BAK'"'"'"'
```

Očekávaný výstup: `The backup set on file 1 is valid.`

### 2. Záloha `bwdata` a aktualizace (jako `bitwarden`, výpadek)

```bash
cd /opt/bitwarden
./bitwarden.sh stop
tar czf ~/bwdata-pre-<verze>-$(date +%F-%H%M).tar.gz -C /opt/bitwarden bwdata && ls -lh ~/bwdata-pre-*.tar.gz
./bitwarden.sh updateself
./bitwarden.sh update
```

Když `tar` selže, nepokračuj a spusť `./bitwarden.sh start`. Archiv potom
zkopíruj mimo server. Kontejnery `bitwarden_sync` (Directory Connector)
a `bitwarden_wazuh_collector` nejsou součástí `bitwarden.sh` a update je nemění.

### 3. Kontrola (jako `afiser`)

```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Status}}' | grep bitwarden
curl -sk https://localhost:6443/api/config | grep -oE '"version":"[^"]+"'
curl -sk -o /dev/null -w '%{http_code}\n' https://localhost:6443/alive
```

Známé hlášky, které nejsou chybou:

- `bitwarden-mssql`: `Login failed for user 'sa'. Reason: Server is in script upgrade mode`
  během upgradu SQL Serveru. Skončí zprávou `Recovery is complete`.
- `bitwarden-api` a `bitwarden-admin`: `LaunchDarkly.Sdk … The SDK key provided is invalid.`

### Obnova databáze

Podle [Backup → Restore](https://bitwarden.com/help/backup-on-premise/), s názvem
databáze `pkpci_vault`:

```bash
docker exec -it bitwarden-mssql bash -c '/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C'
```

```sql
use master
GO
alter database pkpci_vault set offline with rollback immediate
GO
restore database pkpci_vault from disk='/etc/bitwarden/mssql/backups/<soubor>.BAK' with replace
GO
alter database pkpci_vault set online
GO
exit
```

Potom jako `bitwarden` spusť `./bitwarden.sh restart`. Návrat na starší verzi
kontejnerů vyžaduje i obnovu `bwdata` z archivu, protože `update` migruje databázi.

## Stránka o údržbě v Nginx Proxy Manageru

Když kontejner aplikace při deployi neběží, NPM místo bílé stránky
`502 Bad Gateway / openresty` vrátí stránku o údržbě (HTTP 503,
`Retry-After: 20`, automatický refresh po 20 s). Platí pro všechny proxy hosty.
Chybové stránky aplikací se nenahrazují: `proxy_intercept_errors` zůstává
vypnuté, takže 5xx z aplikace projde beze změny. Stránka se zobrazí jen u chyb,
které vygeneruje sám nginx (aplikace neodpovídá nebo neběží).

Soubory jsou v `servery/npm/`:

- `server_proxy.conf` – NPM ho vkládá do každého proxy hostu
  (`/data/nginx/custom/server_proxy.conf`).
- `maintenance.html` – stránka, na serveru jako `/data/custom_pages/__npm_maintenance.html`.
- `render-maintenance.php` – vygeneruje `maintenance.html` z chybové stránky Trenisu
  (`500.phtml` + `@errorBlock.phtml`). Po změně vzhledu chybové stránky v Trenisu
  stránku vygeneruj znovu:

  ```bash
  php servery/npm/render-maintenance.php ../trenis/app/Modules/Presenters/templates/Error > servery/npm/maintenance.html
  ```

- `deploy-maintenance.sh` – nahraje oba soubory do kontejneru
  `nginx-proxy-manager-stack-app-1`, spustí `nginx -t` a `nginx -s reload`.
  Když test konfigurace selže, `server_proxy.conf` smaže.
