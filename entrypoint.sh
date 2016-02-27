#!/bin/bash
: ${VHOSTDIR:=/srv/rproxy/vhost}
: ${NGINXDIR:=/etc/nginx/conf.d}

rm -f ${NGINXDIR}/*.conf

/srv/rproxy/rproxy.py

exec "$@"
