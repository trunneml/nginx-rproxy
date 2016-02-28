FROM nginx:latest
MAINTAINER Michael Trunner <michael@trunner.de>

# Install some debian stuff
COPY apt/* /etc/apt/
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

# Configure Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Install simp_le Let's encrypt/ACME client
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    git \
 && cd /opt/ \
 && git clone https://github.com/kuba/simp_le.git \
 && cd /opt/simp_le \
 && ./bootstrap.sh \
 && ./venv.sh \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

COPY rproxy /srv/rproxy
WORKDIR /srv/rproxy
ENV RPROXY_DOCUMENT_ROOT /srv/rproxy/webroot
ENV RPROXY_SIMP_LE /opt/simp_le/venv/bin/simp_le

VOLUME ["/etc/nginx/conf.d/"]
VOLUME ["/srv/rproxy/vhost/"]

CMD ["/srv/rproxy/rproxy.py", "-vv", "run"]
