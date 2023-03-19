FROM postgres:13

ENV PGDATA=/data/pgdata

# Create a new user
RUN useradd -ms /bin/bash patroni

# Install necessary packages
RUN apt-get update && \
    apt-get install -y python3-pip curl jq libpq-dev && \
    pip3 install patroni[etcd] psycopg2

# Create the /data directory and change its ownership to the patroni user
RUN mkdir /data && \
    chown -R patroni:patroni /data

# Copy the patroni.yaml configuration file
COPY patroni.yml /etc/patroni.yml

# Change the ownership of the configuration file
RUN chown patroni:patroni /etc/patroni.yml

# Expose the necessary ports
EXPOSE 5432 8008

# Switch to the new user
USER patroni

CMD ["patroni", "/etc/patroni.yml"]
