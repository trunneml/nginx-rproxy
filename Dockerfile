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

# Install Forego
RUN wget -P /usr/local/bin https://godist.herokuapp.com/projects/ddollar/forego/releases/current/linux-amd64/forego \
  && chmod u+x /usr/local/bin/forego

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

COPY entrypoint.sh /entrypoint.sh
RUN chmod 755 /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

VOLUME ["/etc/nginx/conf.d/"]
VOLUME ["/srv/rproxy/vhost/"]

CMD ["forego", "start", "-r"]
