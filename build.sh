#!/bin/bash
set -e
docker compose -f docker-compose.yaml build
docker compose -f docker-compose.yaml create --force-recreate
docker image prune --force

