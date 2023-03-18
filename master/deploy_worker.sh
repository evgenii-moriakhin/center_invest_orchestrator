#!/bin/bash

WORKER_GIT_REPO=$1
WORKER_NAME=$2
WORKER_PORT=$3
APP_IMAGE=$4
APP_GIT_REPO=$5
APP_PORT=$6
HEALTHCHECK_API=$7
APP_DOCKERFILE=$8
WORKER_DOCKERFILE=$9


# Remove existing container with the same name if it's running
if docker ps -a --format '{{.Names}}' | grep -Eq "^${WORKER_NAME}\$"; then
  docker rm -f $WORKER_NAME
fi

# Remove containers running worker_image
docker ps -a --filter ancestor=worker_image --format '{{.ID}}' | xargs -r docker rm -f

# Clone worker git repository and build Docker image
rm -rf worker_repo
git clone $WORKER_GIT_REPO worker_repo
cd worker_repo
WORKER_DIR=$(dirname $WORKER_DOCKERFILE)
cp -R "../WORKER_DIR" .
docker build --no-cache -t worker_image -f $WORKER_DOCKERFILE .
cd ..

# Run the Docker container
docker run -d --name $WORKER_NAME -p $WORKER_PORT:$WORKER_PORT \
  -e APP_PORT=$APP_PORT -e HEALTHCHECK_API=$HEALTHCHECK_API -e APP_DOCKERFILE=$APP_DOCKERFILE \
  -e WORKER_PORT=$WORKER_PORT -e APP_GIT_REPO=$APP_GIT_REPO \
  -e APP_IMAGE=$APP_IMAGE -e WORKER_DOCKERFILE=$WORKER_DOCKERFILE -e WORKER_NAME=$WORKER_NAME \
  -v /var/run/docker.sock:/var/run/docker.sock \
  worker_image
