#!/bin/bash

# IPv4 address expected

export TSC_IP=$(tailscale ip | awk 'FNR == 1 {print}')
export TSC_IP_BASE=$(tailscale ip | awk 'NR==1' | grep -oP '^\d+\.\d+')
export FENRIR_DOCKER_NETWORK=$(hostname)-network

docker swarm init --advertise-addr $(echo $TSC_IP)

export DOCKER_LEADER_NODE_ID=$(docker node ls | grep Leader | awk '{print $1}')

docker node update --label-add service=kafka $(echo $DOCKER_LEADER_NODE_ID)

docker network create \
--driver overlay \
--subnet="${TSC_IP_BASE}.0.0/16" \
--gateway=$(echo $TSC_IP) \
--attachable \
--label layer=core \
--scope global \
$(hostname)-network

# in order to use variables from host shell from within docker swarm yaml syntax
# import .env as env_file in kafka-stack.yml in order to use
# ports: \n\t published: ${VARIABLE}
# set -a; . ./.env; set +a
# https://stackoverflow.com/a/58670417
# https://stackoverflow.com/a/58082993 also

docker stack deploy -c ~/.fenrir/kafka/kafka-stack.yml kafka --detach=false

docker stack deploy -c ~/.fenrir/portainer/portainer-stack.yml portainer --detach=false

docker stack deploy -c ~/.fenrir/postgres+metabase/postgres-metabase-stack.yml postgres_metabase --detach=false
