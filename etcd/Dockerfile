FROM quay.io/coreos/etcd:v3.5.1

EXPOSE 2379 2380

CMD ["etcd", "--advertise-client-urls", "http://0.0.0.0:2379", "--listen-client-urls", "http://0.0.0.0:2379"]
