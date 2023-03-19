FROM quay.io/coreos/etcd:v3.5.1

EXPOSE 2379 2380

CMD ["etcd", \
     "--advertise-client-urls", "http://host.docker.internal:2379", \
     "--listen-client-urls", "http://0.0.0.0:2379", \
     "--listen-peer-urls", "http://0.0.0.0:2380", \
     "--initial-advertise-peer-urls", "http://host.docker.internal:2380", \
     "--initial-cluster", "default=http://host.docker.internal:2380", \
     "--enable-v2"]