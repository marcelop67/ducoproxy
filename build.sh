#!/bin/bash
set -e
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml create --force-recreate
docker image prune --force

