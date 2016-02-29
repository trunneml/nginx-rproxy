FROM nginx:latest
MAINTAINER Michael Trunner <michael@trunner.de>

# Install some debian stuff
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

ENV RPROXY_SIMP_LE /opt/simp_le/venv/bin/simp_le
ENV RPROXY_DOCUMENT_ROOT /srv/rproxy/webroot

RUN mkdir -p ${RPROXY_DOCUMENT_ROOT}
COPY rproxy.py /srv/rproxy
COPY templates /srv/rproxy/templates
WORKDIR /srv/rproxy

VOLUME ["/srv/rproxy/vhost/"]

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["/srv/rproxy/rproxy.py", "-vv", "run"]
