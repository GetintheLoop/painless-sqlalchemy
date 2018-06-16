#!/bin/sh

# https://hub.docker.com/_/postgres/
sudo docker run \
  --name pg10 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=test \
  -d mdillon/postgis:10

sudo docker build -t lambda-environment-python -f docker/Dockerfile . &&
sudo docker run \
  --link pg10:postgres \
  -u=$UID:$(id -g $USER) \
  -v $(pwd):/user/project \
  -v ~/.aws:/user/.aws \
  -v ~/.npmrc:/user/.npmrc \
  -it lambda-environment-python

sudo docker stop pg10 -t 0
sudo docker rm -f pg10