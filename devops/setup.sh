#!/bin/bash

# IPv4 address expected
source ./export_vars.sh
# init docker swarm
# $SUDO_PASS needs to be exported manually
sudo docker swarm init --advertise-addr ${TSC_IP}

# docker swarm leader id
export DOCKER_LEADER_NODE_ID=$(docker node ls | grep Leader | awk '{print $1}')


export DEFAULT_PSG_VER=17


# kafka volumes
mkdir -p $FENRIR_ROOT_DIR/kafka/volumes/zookeeper/data
mkdir -p $FENRIR_ROOT_DIR/kafka/volumes/zookeeper/logs
mkdir -p $FENRIR_ROOT_DIR/kafka/volumes/broker-0/data
mkdir -p $FENRIR_ROOT_DIR/kafka/volumes/broker-0/logs
mkdir -p $FENRIR_ROOT_DIR/kafka/volumes/connect/jars

# metabase volumes
mkdir -p $FENRIR_ROOT_DIR/analytics/volumes/metabase/data

# devbox
mkdir -p $FENRIR_ROOT_DIR/devbox/volumes/data

# portainer
mkdir -p $FENRIR_ROOT_DIR/portainer/volumes/data

# postgres
mkdir -p $FENRIR_ROOT_DIR/postgres/volumes/${DEFAULT_PSG_VER}

# tailscale
mkdir -p $FENRIR_ROOT_DIR/tailscale/volumes/data

# spark
mkdir -p $FENRIR_ROOT_DIR/spark/volumes/data
mkdir -p $FENRIR_ROOT_DIR/spark/volumes/jars
mkdir -p $FENRIR_ROOT_DIR/spark/volumes/logs

# flink
mkdir -p $FENRIR_ROOT_DIR/flink/volumes/taskmanager/state
mkdir -p $FENRIR_ROOT_DIR/flink/volumes/jobmanager/state


# update for restraints
docker node update --label-add kafka=true $DOCKER_LEADER_NODE_ID
docker node update --label-add dev=true $DOCKER_LEADER_NODE_ID
docker node update --label-add airflow=true $DOCKER_LEADER_NODE_ID
docker node update --label-add analytics=true $DOCKER_LEADER_NODE_ID
docker node update --label-add postgres=true $DOCKER_LEADER_NODE_ID
docker node update --label-add spark=true $DOCKER_LEADER_NODE_ID
docker node update --label-add flink=true $DOCKER_LEADER_NODE_ID


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

docker stack deploy -c ${FENRIR_ROOT_DIR}/airflow/airflow-stack.yml airflow --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/devbox/devbox-stack.yml devbox --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/spark/spark-stack.yml spark --detach=false

docker stack deploy -c ${FENRIR_ROOT_DIR}/flink/flink-stack.yml flink --detach=false
