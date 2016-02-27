#!/usr/bin/env python
import argparse
import json
import logging
import os
import sys

logger = logging.getLogger(__name__ if __name__ != '__main__' else 'RProxy')


def read_file(filepath):
    logger.debug("Reading file: %s", filepath)
    with open(filepath, 'r') as readfile:
        return readfile.read()


class ReverseProxyConfigGernerator(object):

    class VhostError(Exception):
        pass

    class ConfigError(Exception):
        pass

    HTTP_TMPL = 'rproxy-80.conf'
    HTTPS_TMPL = 'rproxy-443.conf'
    CERT_FILE = 'fullchain.pem'
    KEY_FILE = 'key.pem'

    def __init__(self, template_dir, vhost_dir, nginx_conf_dir):
        if not os.path.isdir(nginx_conf_dir):
            raise self.ConfigError("NGINX config path must be a directory")
        self.nginx_conf_dir = nginx_conf_dir
        if not os.path.isdir(vhost_dir):
            raise self.ConfigError("Vhost config path must be a directory")
        self.vhost_dir = vhost_dir
        logger.info("Initializing templates from %s", template_dir)
        try:
            self.http_template = read_file(
                os.path.join(template_dir, self.HTTP_TMPL))
            self.https_template = read_file(
                os.path.join(template_dir, self.HTTPS_TMPL))
        except IOError as ioe:
            logger.error(ioe)
            raise self.ConfigError("Coundn't read nginx templates")

    def read_vhost_config(self, vhost):
        logger.debug("Reading vhost config of %s", vhost)
        vhost_conf_filepath = os.path.join(self.vhost_dir, vhost, 'conf')
        try:
            with open(vhost_conf_filepath, 'r') as vhostfile:
                return json.load(vhostfile)
        except IOError as ioe:
            logger.error(ioe)
            raise self.VhostError(
                "Coundn't read vhost config of %s" % vhost, ioe)

    def hasCertificate(self, vhost):
        key_file = os.path.join(self.vhost_dir, vhost, self.KEY_FILE)
        cert_file = os.path.join(self.vhost_dir, vhost, self.CERT_FILE)
        return os.path.isfile(key_file) and os.path.isfile(cert_file)

    def configure_vhost(self, vhost):
        logger.info("Generating vhost config for %s", vhost)
        vhost_config = self.read_vhost_config(vhost)
        if self.hasCertificate(vhost):
            logger.debug("Using HTTPS template for %s", vhost)
            nginx_tmpl = self.https_template
        else:
            logger.debug("Using HTTP template for %s", vhost)
            nginx_tmpl = self.http_template
        try:
            nginx_conf = nginx_tmpl % vhost_config
        except KeyError as ke:
            raise self.VhostError(
                "Missing config parameters for vhost %s" % vhost, ke)
        self.write_nginx_config(vhost, nginx_conf)

    def write_nginx_config(self, vhost, config):
        try:
            nginx_filepath = os.path.join(self.nginx_conf_dir,
                                          "%s.conf" % vhost)
            logger.debug("Writting nginx config file: %s", nginx_filepath)
            with open(nginx_filepath, 'w') as nginx_file:
                nginx_file.write(config)
        except IOError as ioe:
            logger.error(ioe)
            raise self.VhostError(
                "Couldn't write NGinx config file %s" % vhost, ioe)

    def configure_all_vhosts(self):
        vhosts = [vh for vh in os.listdir(self.vhost_dir)
                  if os.path.isdir(os.path.join(self.vhost_dir, vh))]
        for vhost in vhosts:
            try:
                self.configure_vhost(vhost)
            except self.VhostError as vh:
                logger.warn(vh)  # pylint: disable=no-member


def main():
    template_dir = os.environ.get('RPROXY_TMPL_DIR', 'templates')
    nginx_conf_dir = os.environ.get('NGINX_CONF_DIR', '/etc/nginx/conf.d')
    vhost_dir = os.environ.get('VHOST_DIR', 'vhost')

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase output verbosity")
    parser.add_argument("-t", "--templates", default=template_dir,
                        help="path to the template directory")
    parser.add_argument("-c", "--vhostdir", default=vhost_dir,
                        help="path to the vhost directory")
    parser.add_argument("--nginxconfd", default=nginx_conf_dir,
                        help="path to the nginx conf.d directory")
    args = parser.parse_args()

    if args.verbosity == 0:
        logging.basicConfig(level=logging.WARN)
    elif args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)

    try:
        rproxy = ReverseProxyConfigGernerator(
            args.templates, args.vhostdir, args.nginxconfd)
        rproxy.configure_all_vhosts()
    except ReverseProxyConfigGernerator.ConfigError as ce:
        logger.error(ce)  # pylint: disable=no-member
        sys.exit(1)


if __name__ == "__main__":
    main()
