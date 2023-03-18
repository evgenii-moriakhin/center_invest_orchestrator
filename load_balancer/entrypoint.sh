#!/bin/sh
set -e

log() {
    echo "$(date +"%Y-%m-%d %H:%M:%S") $1"
}

# Fetch hosts and create a server block for each
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

    rm -f /etc/nginx/conf.d/*.conf
    for host in $hosts; do
        upstream_url=$host
        log "Creating server block for host: $host"

        # Replace colons with underscores for file and upstream names
        file_name=$(echo $host | tr ':' '_')
        upstream_name=$(echo ${host}_backend | tr ':' '_')

cat > /etc/nginx/conf.d/${file_name}.conf <<EOL
upstream $upstream_name {
    server $upstream_url;
}

server {
    listen 80;
    server_name $file_name;

    location / {
        proxy_pass http://$upstream_name;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL
    done
}

# Fetch initial hosts and reload nginx
fetch_hosts || true
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
    fetch_hosts || true
    log "Reloading Nginx configuration"
    nginx -s reload
    log "Sleeping for 5 minutes"
    sleep 300 # Sleep for 5 minutes
  done
) &

# Keep the script running
wait
