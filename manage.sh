#!/bin/sh

# https://hub.docker.com/_/postgres/
docker run \
  --name pg10 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=test \
  -d mdillon/postgis:10

docker build -t lambda-environment-python -f docker/Dockerfile . &&
docker run \
  --link pg10:postgres \
  -u=$UID:$(id -g $USER) \
  -v $(pwd):/user/project \
  -v ~/.aws:/user/.aws \
  -v ~/.npmrc:/user/.npmrc \
  -it lambda-environment-python

docker stop pg10 -t 0
docker rm -f pg10