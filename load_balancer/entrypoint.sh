#!/bin/bash
set -e

log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") $1"
}

# Fetch hosts and create an upstream block
fetch_hosts() {
    log "Fetching hosts from API"
    response=$(curl -s -f -S $API_URL 2>&1)
    ret=$?
    if [ $ret -ne 0 ]; then
        log "Error: Failed to fetch hosts from API: $response"
        return $ret
    fi

    hosts=$(echo $response | jq -r '.[]')
    ret=$?
    if [ $ret -ne 0 ]; then
        log "Error: Failed to parse hosts from API response: $hosts"
        return $ret
    fi

    upstream_block=$(printf "upstream backend {\n")
    for host in $hosts; do
        if [[ "$host" == 127.0.0.1* ]]; then
            host=${host/127.0.0.1/host.docker.internal}
        fi
        log "Adding host to upstream block: $host"
        upstream_block=$(printf "%s    server %s;\n" "$upstream_block" "$host")
    done
    upstream_block=$(printf "%s}\n" "$upstream_block")
    echo "$upstream_block" > /etc/nginx/conf.d/upstream.conf
}

# Fetch initial hosts and reload nginx
fetch_hosts  true
log "Reloading Nginx configuration"
nginx -c /etc/nginx/nginx.conf -t # Test the configuration

# Create the PID file
touch /var/run/nginx.pid

# Start Nginx in the background
log "Starting Nginx"
nginx -c /etc/nginx/nginx.conf -g "daemon off;" &

# Set up a periodic task to fetch hosts and reload nginx
(
  while true; do
    fetch_hosts  true
    log "Reloading Nginx configuration"
    nginx -s reload
    log "Sleeping for 5 minutes"
    sleep 300 # Sleep for 5 minutes
  done
) &

# Keep the script running
wait