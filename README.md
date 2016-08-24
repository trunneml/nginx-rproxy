[![](https://images.microbadger.com/badges/version/trunneml/nginx-rproxy.svg)](http://microbadger.com/images/trunneml/nginx-rproxy "Get your own version badge on microbadger.com")

# nginx-rproxy

nginx-rproxy is a docker image that contains a python program to configure and
start nginx as a reverse proxy. One of it's main features is the automatic
TLS/SSL certificate creation using let's encrypt.
It is inspired by https://github.com/jwilder/nginx-proxy, but uses an explicit configuration with docker network support instead of a complex container auto detection that has problems with the new docker network feature.


## Features

* Based on the **official nginx** docker image
* **docker network support** (even overlay)
* TLS/SSL termination
* Maps domains to the related application server
* Simple **Json configuration**
* **HTTPS support** (when certificate is present)
* **HTTP to HTTS redirect**
* Auto TLS/SSL **certificate creation using Let's encrypt**
* Restarts nginx when needed
* Monitors and restarts nginx (on crash)


## Usage

nginx-rproxy is designed as a reverse proxy with TLS/SSL termination in front
of your other web applications. nginx-rproxy maps the request based on the
domain to the real web application. Normally these applications are also docker
containers.

nginx-rproxy is configured by JSON config files. Each config file represents a vhost, that maps the defined domains to a coonected HTTP server.


## Installation and configuration

1. nginx-rproxy is available on docker hub, so just pull the latest release.

   ```sh
   $ docker pull trunneml/nginx-rproxy:latest
   ```

2. For each ``vhost`` create a folder inside your docker host.

   ```sh
   $ mkdir -p /srv/nginx-rproxy/vhost/mynewvhost
   ```

   Put a file named ``conf`` in that folder:

   ```sh
   $ cat >/srv/nginx-rproxy/vhost/mynewhost/conf << EOL
   {
     "domains": ["example.com", "www.example.com"],
     "target": "container1.rproxynet",
     "letsencrypt": true,
     "email": "info@example.com"
   }
   EOL
   ```

3. Create a new docker network and  run the nginx-rproxy container with the created config mounted.

   ```sh
   $ docker network create rproxynet
   ```

   ```sh
   $ docker run -d -p 80:80 -p 443:443 --name rproxy --network rproxynet -v /srv/nginx-rproxy/vhost:/srv/rproxy/vhost trunneml/nginx-rproxy:latest
   ```

4. Connect your application server docker containers to the ``rproxynet``

  ```sh
  $ docker network connect rproxynet <app_container>
  ```

  **Note:** You have to start your app container first.


## Development and contribution

For development checkout the code from the github repository and create the
Python 3 venv by the included shell script.

```sh
$ git clone https://github.com/trunneml/nginx-rproxy.git
...
$ cd nginx-rproxy
$ ./setup_venv
```

To upgrade the python dependencies run the following shell script. It will
download the latest dependencies and updates your local venv.

```sh
$ ./upgrade_venv
```


## License

Copyright (C) 2016 Michael Trunner

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
