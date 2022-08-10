#!/bin/bash
set -e
docker pull marcelop67/ducoproxy:latest
docker-compose stop
docker-compose rm --force
docker-compose up -d --force-recreate
