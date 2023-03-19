FROM nginx:latest
RUN apt-get update && apt-get install -y curl jq
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV API_URL="http://host.docker.internal:8000/healthy_hosts"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-c", "/etc/nginx/nginx.conf", "-g", "daemon off;"]