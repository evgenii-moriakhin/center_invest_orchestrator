FROM postgres:13

ENV PGDATA=/data/pgdata

RUN apt-get update && \
    apt-get install -y python3-pip curl jq && \
    pip3 install patroni[etcd]

COPY patroni.yml /etc/patroni.yml

EXPOSE 5432 8008

CMD ["patroni", "/etc/patroni.yml"]
