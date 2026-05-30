#!/bin/bash

case "$1" in
  start)
    docker build -t livros-api:latest .
    docker swarm init
    docker stack deploy -c docker-stack.yml livros
    ;;
  status)
    docker stack ps livros
    ;;
  scale)
    docker service scale livros_web=$2
    ;;
  stop)
    docker stack rm livros
    docker swarm leave --force
    ;;
  *)
    echo "Uso: ./swarm.sh [start|status|scale N|stop]"
    ;;
esac