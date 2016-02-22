FROM nginx:latest
MAINTAINER Michael Trunner <michael@trunner.de>

# Install some debian stuff
COPY testing.list /etc/apt/sources.list.d/
COPY apt_preferences /etc/apt/preferences
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

COPY app /srv/rproxy
WORKDIR /srv/rproxy

VOLUME ["/etc/nginx/conf.d/"]
VOLUME ["/srv/rproxy/conf.d/"]

CMD ["forego", "start", "-r"]
