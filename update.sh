#!/bin/bash
set -e
IMAGE=$(grep -oP "image: \K.+" docker-compose.yaml)
docker pull $IMAGE
docker-compose stop
docker-compose rm --force
docker-compose up -d --force-recreate
docker image prune --force

