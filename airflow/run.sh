#!/bin/bash

docker stack deploy -c airflow-stack.yml -d=false airflow
