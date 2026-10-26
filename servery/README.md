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
