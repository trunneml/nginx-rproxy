# nginx-rproxy
nginx-rproxy is a Docker image that contains a python program to configure and starting nginx as a reverse proxy.
It supports SSL certificate creation with let's encrypt and restarts nginx in case of an error.

## Features:

* Simple **Json configuration**
* **HTTPS support** when certificate is present
* HTTP to HTTS redirect
* Auto SSL certificate creation with **Let's encrypt**
* Restart nginx when needed
* Monitors nginx if it crashes


**Note:** This project is in an early state, but is in production use.

## TODOs

* Reduce disk space by replacing simp_le
* Improved logging output
* Write some test
* Write setup.py
