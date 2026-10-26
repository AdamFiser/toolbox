#!/usr/bin/env bash
# Aktualizace Portaineru: server na docker.pkpcargointernational.com,
# potom agenti na ostatních docker hostech na stejnou verzi jako server.
#
# Použití: ./update-portainer.sh [server|agents|all]   (výchozí all)
# Proměnné: SSH_KEY, SERVER_HOST, AGENT_HOSTS (mezerou oddělený seznam user@host)
set -euo pipefail

SSH_KEY=${SSH_KEY:-~/.ssh/id_ed25519_toolbox}
SERVER_HOST=${SERVER_HOST:-afiser@docker.pkpcargointernational.com}
SERVER_URL=${SERVER_URL:-https://docker.pkpcargointernational.com:9443}
read -ra AGENT_HOSTS <<<"${AGENT_HOSTS:-aiops@bestie.pkpcargointernational.com}"

here=$(dirname "$0")

remote() {
	local host=$1
	shift
	ssh -i "$SSH_KEY" -o BatchMode=yes "$host" bash -s -- "$@" <"$here/recreate-container.sh"
}

server_version() {
	curl -sk -m 10 "$SERVER_URL/api/system/status" | sed -E 's/.*"Version":"([^"]+)".*/\1/'
}

update_server() {
	remote "$SERVER_HOST" portainer portainer/portainer-ce:lts portainer_data \
		--restart=always -p 8000:8000 -p 9443:9443 \
		-v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data
	echo "Portainer server: $(server_version)"
}

update_agents() {
	local version
	version=$(server_version)
	[[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Nezjistím verzi serveru z $SERVER_URL" >&2; exit 1; }
	for host in "${AGENT_HOSTS[@]}"; do
		remote "$host" portainer_agent "portainer/agent:$version" - \
			--restart=always -p 9001:9001 \
			-v /var/run/docker.sock:/var/run/docker.sock \
			-v /var/lib/docker/volumes:/var/lib/docker/volumes
	done
	echo "Portainer UI ukáže novou verzi agentů až po dalším snapshotu (interval 5 min)."
}

case ${1:-all} in
	server) update_server ;;
	agents) update_agents ;;
	all) update_server && update_agents ;;
	*) echo "Použití: $0 [server|agents|all]" >&2; exit 2 ;;
esac
