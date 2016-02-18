FROM nginx:latest
MAINTAINER Michael Trunner <michael@trunner.de>

# Install letsencrypt and some other stuff
COPY testing.list /etc/apt/sources.list.d/
COPY apt_preferences /etc/apt/preferences
RUN apt-get update \
 && apt-get install -y -q --no-install-recommends \
    ca-certificates \
    wget \
 && apt-get install -y -q --no-install-recommends -t testing letsencrypt \
 && apt-get clean \
 && rm -r /var/lib/apt/lists/*

# Install Forego
RUN wget -P /usr/local/bin https://godist.herokuapp.com/projects/ddollar/forego/releases/current/linux-amd64/forego \
  && chmod u+x /usr/local/bin/forego

# Configure Nginx
COPY nginx.conf /etc/nginx/nginx.conf

COPY app /app
WORKDIR /app

VOLUME ["/etc/nginx/conf.d/"]
VOLUME ["/etc/letsencrypt/"]

CMD ["forego", "start", "-r"]
