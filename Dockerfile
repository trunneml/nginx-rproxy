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

# Install free_tls_certificates
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python-dev \
    python-pip \
    python-wheel \
    python-setuptools \
&& pip install free_tls_certificates

# Workaround for: https://github.com/mail-in-a-box/free_tls_certificates/pull/12
# Workaround for: https://github.com/mail-in-a-box/free_tls_certificates/pull/9
RUN pip install acme==0.20.0

ENV RPROXY_DOCUMENT_ROOT /srv/rproxy/webroot

RUN mkdir -p ${RPROXY_DOCUMENT_ROOT}
COPY rproxy.py /srv/rproxy/rproxy.py
COPY templates /srv/rproxy/templates
WORKDIR /srv/rproxy

VOLUME ["/srv/rproxy/vhost/"]

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 80 443

CMD ["/srv/rproxy/rproxy.py", "-v", "run"]
