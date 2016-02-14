FROM nginx:latest
MAINTAINER Michael Trunner <michael@trunner.de>

# Install wget and install/updates certificates
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


COPY . /app
WORKDIR /app

VOLUME ["/etc/nginx/conf.d/"]

CMD ["forego", "start", "-r"]
