#!/usr/bin/env bash
# Nahraje stránku o údržbě a server_proxy.conf do NPM na serveru docker.
# Když nginx -t selže, konfiguraci smaže a NPM nechá beze změny.
set -euo pipefail

HOST="${HOST:-afiser@docker.pkpcargointernational.com}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519_toolbox}"
CONTAINER="${CONTAINER:-nginx-proxy-manager-stack-app-1}"
DIR="$(cd "$(dirname "$0")" && pwd)"

remote() { ssh -i "$SSH_KEY" -o BatchMode=yes "$HOST" "$@"; }

remote "docker exec $CONTAINER mkdir -p /data/custom_pages /data/nginx/custom"
remote "docker exec -i $CONTAINER sh -c 'cat > /data/custom_pages/__npm_maintenance.html'" < "$DIR/maintenance.html"
remote "docker exec -i $CONTAINER sh -c 'cat > /data/nginx/custom/server_proxy.conf'" < "$DIR/server_proxy.conf"

if ! remote "docker exec $CONTAINER nginx -t"; then
	remote "docker exec $CONTAINER rm -f /data/nginx/custom/server_proxy.conf"
	echo "nginx -t selhal, server_proxy.conf odstraněn." >&2
	exit 1
fi

remote "docker exec $CONTAINER nginx -s reload"
echo "Hotovo: stránka o údržbě je aktivní pro všechny proxy hosty."
