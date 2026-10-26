#!/usr/bin/env bash
# Běží NA SERVERU (posílá ho update-portainer.sh přes `ssh ... bash -s`).
# Stáhne image a kontejner znovu vytvoří, jen pokud je image novější.
# Při neúspěchu vrátí původní kontejner.
#
# Použití: recreate-container.sh <název> <image> <volume-k-záloze|-> [docker run argumenty...]
set -euo pipefail

name=$1 image=$2 backup_volume=$3
shift 3

docker=docker
$docker info >/dev/null 2>&1 || docker="sudo -n docker"

$docker pull -q "$image" >/dev/null
new_id=$($docker image inspect "$image" --format '{{.Id}}')
cur_id=$($docker inspect "$name" --format '{{.Image}}' 2>/dev/null || true)
[ -n "$cur_id" ] || { echo "$(hostname): kontejner $name neexistuje" >&2; exit 1; }

if [ "$new_id" = "$cur_id" ]; then
	echo "$(hostname): $name už běží na aktuální $image"
	exit 0
fi

$docker stop "$name" >/dev/null

if [ "$backup_volume" != "-" ]; then
	dir=~/backups/portainer
	mkdir -p "$dir"
	file=portainer_data-$(date +%Y%m%d-%H%M%S).tar.gz
	$docker run --rm -v "$backup_volume":/data:ro -v "$dir":/backup alpine tar czf "/backup/$file" -C /data .
	echo "$(hostname): záloha $backup_volume -> $dir/$file"
fi

$docker rename "$name" "$name-old"
if $docker run -d --name "$name" "$@" "$image" >/dev/null && sleep 10 \
	&& [ "$($docker inspect "$name" --format '{{.State.Running}}')" = true ]; then
	$docker rm "$name-old" >/dev/null
	echo "$(hostname): $name aktualizován na $image"
else
	echo "$(hostname): $name se nespustil, vracím původní kontejner" >&2
	$docker logs --tail 20 "$name" >&2 || true
	$docker rm -f "$name" >/dev/null 2>&1 || true
	$docker rename "$name-old" "$name"
	$docker start "$name" >/dev/null
	exit 1
fi
