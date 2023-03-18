#!/bin/bash

while true; do
  echo "$(date -Iseconds) Fetching hosts from API"
  hosts=$(curl -s "$API_URL")
  if [ ! -z "$hosts" ]; then
    echo "$(date -Iseconds) Creating upstream block for healthy hosts"
    upstream_block="upstream backend {\n"
    for host in $(echo "$hosts" | jq -r '.[]'); do
      upstream_block+="  server $host;\n"
    done
    upstream_block+="}"
    echo -e "$upstream_block" > /etc/nginx/conf.d/upstream.conf

    echo "$(date -Iseconds) Reload#!/bin/bash

while true; do
  echo "$(date -Iseconds) Fetching hosts from API"
  hosts=$(curl -s "$API_URL")
  if [ ! -z "$hosts" ]; then
    echo "$(date -Iseconds) Creating upstream block for healthy hosts"
    upstream_block="upstream backend {\n"
    for host in $(echo "$hosts" | jq -r '.[]'); do
      upstream_block+="  server $host;\n"
    done
    upstream_block+="}"
    echo -e "$upstream_block" > /etc/nginx/conf.d/upstream.conf

    echo "$(date -Iseconds) Reloading Nginx configuration"
    nginx -t && nginx -s reload
  else
    echo "$(date -Iseconds) No healthy hosts found, skipping Nginx configuration update"
  fi
  echo "$(date -Iseconds) Sleeping for 5 minutes"
  sleep 300
doneing Nginx configuration"
    nginx -t && nginx -s reload
  else
    echo "$(date -Iseconds) No healthy hosts found, skipping Nginx configuration update"
  fi
  echo "$(date -Iseconds) Sleeping for 5 minutes"
  sleep 300
done
