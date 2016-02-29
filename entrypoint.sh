#!/bin/bash

__create_dhparams() {
  test -f /srv/rproxy/vhost/dhparams.pem || openssl dhparam -out /srv/rproxy/vhost/dhparams.pem 2048
}

__create_dhparams

exec "$@"
