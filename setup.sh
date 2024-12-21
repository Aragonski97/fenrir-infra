#!/bin/bash

# IPv4 address expected

export TSC_IP=$(tailscale ip | awk 'FNR == 1 {print}')
export TSC_IP_BASE=$(tailscale ip | awk 'NR==1' | grep -oP '^\d+\.\d+')
export FENRIR_DOCKER_NETWORK=$(hostname)-network
export FENRIR_ROOT_DIR=$(pwd)

# init docker swarm
docker swarm init --advertise-addr ${TSC_IP}

# docker swarm leader id
export DOCKER_LEADER_NODE_ID=$(docker node ls | grep Leader | awk '{print $1}')


# update for restraints
docker node update --label-add kafka=true $DOCKER_LEADER_NODE_ID
docker node update --label-add dev=true $DOCKER_LEADER_NODE_ID
docker node update --label-add airflow=true $DOCKER_LEADER_NODE_ID
docker node update --label-add analytics=true $DOCKER_LEADER_NODE_ID
docker node update --label-add postgres=true $DOCKER_LEADER_NODE_ID


# create network for swarm
docker network create \
--driver overlay \
--subnet="${TSC_IP_BASE}.0.0/16" \
--gateway=$TSC_IP \
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

# deployment

docker stack deploy -c ${FENRIR_ROOT_DIR}/kafka/kafka-stack.yml kafka --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/portainer/portainer-stack.yml portainer --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/postgres/postgres-stack.yml postgres --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/analytics/metabase-stack.yml metabase --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/airflow/local-executor-airflow-stack.yml airflow --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/devbox/devbox-stack.yml devbox --detach=false
