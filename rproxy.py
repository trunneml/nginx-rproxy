#!/usr/bin/env python
import argparse
import ctypes
import datetime
import json
import logging
import os
import signal
import subprocess
import sys

logger = logging.getLogger('RProxy' if __name__ == '__main__' else __name__)


libc = ctypes.CDLL("libc.so.6")


def set_pdeathsig(sig=signal.SIGTERM):
    """
    For more information see: http://stackoverflow.com/a/19448096
    """
    def func():
        return libc.prctl(1, sig)
    return func


def read_file(filepath):
    logger.debug("Reading file: %s", filepath)
    with open(filepath, 'r') as readfile:
        return readfile.read()


class ConfigError(Exception):
    pass


class Vhost(object):

    def __init__(self, vhost_folder):
        self.folder = os.path.abspath(vhost_folder)
        self.name = os.path.basename(vhost_folder)
        config = self._read_config()
        try:
            self.email = config['email']
            self.target = config['target']
            self.domains = config['domains']
            if not isinstance(self.domains, list):
                raise ConfigError("domains must be a list", self)
            if not self.domains:
                raise ConfigError("domains must not be empty", self)
            self.letsencrypt = config.get('letsencrypt', False)
        except KeyError as ke:
            raise ConfigError("Missing config parameter %s in %s" % (ke, self))

    def _read_config(self):
        logger.debug("Reading vhost config of %s", self)
        vhost_conf_filepath = os.path.join(self.folder, 'conf')
        try:
            with open(vhost_conf_filepath, 'r') as vhostfile:
                return json.load(vhostfile)
        except IOError as ioe:
            logger.error(ioe)
            raise ConfigError(
                "Coundn't read vhost config of %s" % self, ioe)
        except ValueError as jsonerr:
            logger.error(jsonerr)
            raise ConfigError(
                "Coundn't read JSON from vhost config of %s" % self, jsonerr)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def get_vhosts(vhost_dir):
    logger.info("Reading all vhosts from %s", vhost_dir)
    return [Vhost(os.path.join(vhost_dir, vh)) for vh in os.listdir(vhost_dir)
            if os.path.isdir(os.path.join(vhost_dir, vh))]


class ConfigGeneratorError(Exception):
    pass


class NginxConfigGenerator(object):

    HTTP_TMPL = 'http.conf.tmpl'
    HTTPS_TMPL = 'https.conf.tmpl'
    CERT_FILE = 'fullchain.pem'
    KEY_FILE = 'key.pem'

    def __init__(self, template_dir, nginx_conf_dir, document_root):
        if not os.path.isdir(nginx_conf_dir):
            raise ConfigError("NGINX config path must be a directory")
        self.nginx_conf_dir = nginx_conf_dir
        if not os.path.isdir(document_root):
            raise ConfigError("document_root must be a directory")
        self.document_root = document_root
        logger.info("Initializing templates from %s", template_dir)
        try:
            self.http_template = read_file(
                os.path.join(template_dir, self.HTTP_TMPL))
            self.https_template = read_file(
                os.path.join(template_dir, self.HTTPS_TMPL))
        except IOError as ioe:
            logger.error(ioe)
            raise ConfigError("Coundn't read nginx templates")

    def hasCertificate(self, vhost):
        key_file = os.path.join(vhost.folder, self.KEY_FILE)
        cert_file = os.path.join(vhost.folder, self.CERT_FILE)
        return os.path.isfile(key_file) and os.path.isfile(cert_file)

    def configure_vhost(self, vhost):
        logger.info("Generating vhost config for %s", vhost)
        if self.hasCertificate(vhost):
            logger.debug("Using HTTPS template for %s", vhost)
            nginx_tmpl = self.https_template
        else:
            logger.debug("Using HTTP template for %s", vhost)
            nginx_tmpl = self.http_template
        try:
            nginx_conf = nginx_tmpl % {'servernames': ' '.join(vhost.domains),
                                       'target': vhost.target,
                                       'document_root': self.document_root,
                                       'vhost': vhost.name}
        except KeyError as ke:
            raise ConfigGeneratorError(
                "Missing config parameters for vhost %s" % vhost, ke)
        self.write_nginx_config(vhost, nginx_conf)

    def write_nginx_config(self, vhost, config):
        try:
            nginx_filepath = os.path.join(self.nginx_conf_dir,
                                          "%s.conf" % vhost.name)
            logger.debug("Writting nginx config file: %s", nginx_filepath)
            with open(nginx_filepath, 'w') as nginx_file:
                nginx_file.write(config)
        except IOError as ioe:
            logger.error(ioe)
            raise ConfigGeneratorError(
                "Couldn't write NGinx config file %s" % vhost, ioe)

    def clean_config_dir(self):
        logger.info("Removing old conf files in %s", self.nginx_conf_dir)
        for old_conf_file in os.listdir(self.nginx_conf_dir):
            if old_conf_file.endswith(".conf"):
                filepath = os.path.abspath(
                    os.path.join(self.nginx_conf_dir, old_conf_file))
                logger.debug("Removing old config file %s", filepath)
                os.remove(filepath)


class CertGenerationError(Exception):
    pass


class SimpLeCertGenerator(object):

    TESTING = "https://acme-staging.api.letsencrypt.org/directory"

    def __init__(self, simp_le_path, document_root, testing):
        self.simp_le_path = simp_le_path
        if not os.path.isdir(document_root):
            raise ConfigError("document_root must be a directory")
        self.document_root = document_root
        self.testing = testing

    def generate_cert(self, vhost):
        """
        Returns True when a new cert was created,
        False when no update is needed.
        """
        logger.info("Generating new let's encrypt certificate for %s", vhost)
        cmd = [self.simp_le_path, "--default_root", self.document_root,
               "-f", "account_key.json",
               "-f", "fullchain.pem", "-f", "key.pem"]
        if self.testing:
            logger.warn("Using ACME staging directory!")
            cmd.extend(("--server", self.TESTING))
        cmd.extend(("--email", vhost.email))
        for domain in vhost.domains:
            cmd.extend(("-d", domain))
        logger.debug("Calling command: %s", cmd)
        try:
            exit_code = subprocess.call(cmd, cwd=vhost.folder)
        except OSError as ose:
            raise CertGenerationError(
                "Error while generating cert for %s", ose)
        logger.debug("Command exit code was: %i", exit_code)
        if exit_code >= 2:
            raise CertGenerationError(
                "Error %i while generating cert for %s"
                % (exit_code, vhost.domains))
        if exit_code == 0:
            logger.info("New certificate generated for %s", vhost)
        return exit_code == 0


class RProxy(object):

    NGINX_START = ['nginx', '-g', "daemon off;"]

    def __init__(self, cert_generator, config_generator, vhosts):
        self.cert_generator = cert_generator
        self.config_generator = config_generator
        self.vhosts = vhosts
        self._next_run = datetime.datetime.now()
        self._nginx = None

    def init_config(self):
        self.config_generator.clean_config_dir()
        for vhost in self.vhosts:
            try:
                self.config_generator.configure_vhost(vhost)
            except ConfigGeneratorError as vhe:
                logger.error(vhe)

    def _restart_nginx(self):
        if self._nginx and self._nginx.poll() is not None:
            logger.critical(
                "NGINX died with exit_code %s", self._nginx.returncode)
            self._nginx = None
        if not self._nginx:
            logger.info("Starting nginx")
            self._nginx = subprocess.Popen(
                self.NGINX_START, preexec_fn=set_pdeathsig(signal.SIGTERM))
        else:
            logger.debug("Sending SIGHUP to nginx for a config reload")
            self._nginx.send_signal(signal.SIGHUP)

    def run(self):
        def receive_alarm(signum, stack):  # pylint: disable=unused-argument
            """
            Will be trigged by SIGALRM and generates new nginx cers and config
            """
            logger.debug("SIGNAL %s received by SIGALRM handler", signum)
            self._update_config()
            signal.alarm(3600)
        signal.signal(signal.SIGALRM, receive_alarm)
        # Wait sometime so nginx is ready for acme challange
        signal.alarm(5)
        while True:
            self._restart_nginx()
            self._nginx.wait()  # Wait for SIGALRM or NGINX dies

    def _update_config(self):
        if datetime.datetime.now() < self._next_run:
            logger.debug("To early for a cert update.")
            return

        nginx_reload = False
        for vhost in self.vhosts:
            if vhost.letsencrypt:
                nginx_reload = nginx_reload or self._new_cert_and_config(vhost)
        if nginx_reload:
            logger.debug("NGINX needs a reload")
            self._restart_nginx()
        self._schedule_next_cert_update()

    def _schedule_next_cert_update(self):
        nd = datetime.date.today() + datetime.timedelta(days=1)
        self._next_run = datetime.datetime(
            year=nd.year, month=nd.month, day=nd.day, hour=2)
        logger.debug("Next run scheduled for: %s", self._next_run)

    def _new_cert_and_config(self, vhost):
        try:
            if not self.cert_generator.generate_cert(vhost):
                return False
            self.config_generator.configure_vhost(vhost)
            return True
        except CertGenerationError as cge:
            logger.warn(cge)
            return False
        except ConfigGeneratorError as vhe:
            logger.error(vhe)
            return False


def _get_args():
    parser = argparse.ArgumentParser(
        description="Helper that generates nginx reverse proxy settings and "
                    "let's encrypt certificates based on simple json files.")
    parser.add_argument("-v", "--verbosity", action="count", default=0,
                        help="increase output verbosity")

    template_dir = os.environ.get('RPROXY_TEMPLATES', 'templates')
    parser.add_argument("-t", "--templates", default=template_dir,
                        help=argparse.SUPPRESS)

    vhost_dir = os.environ.get('RPROXY_VHOSTDIR', 'vhost')
    parser.add_argument("-c", "--vhostdir", default=vhost_dir,
                        help="path to the vhost directory")

    nginx_conf_dir = os.environ.get('RPROXY_NGINXCONFD', '/etc/nginx/conf.d')
    parser.add_argument("-n", "--nginxconfd", default=nginx_conf_dir,
                        help="path to the nginx conf.d directory")

    simp_le = os.environ.get('RPROXY_SIMP_LE', 'simp_le')
    parser.add_argument("-s", "--simp_le", default=simp_le,
                        help="path to simp_le acme client")

    document_root = os.environ.get(
        'RPROXY_DOCUMENT_ROOT', os.path.abspath('webroot'))
    parser.add_argument("-r", "--document_root", default=document_root,
                        help="path to document_root")

    testing = os.environ.get('RPROXY_TESTING', None)
    parser.add_argument("--testing", default=testing,
                        help="path to document_root")

    parser.add_argument("mode", choices=['init', 'run'],
                        help="defines the mode of rproxy")
    return parser.parse_args()


def _configure_logging(args):
    if args.verbosity == 0:
        logging.basicConfig(level=logging.WARN)
    elif args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)


def main():
    args = _get_args()

    _configure_logging(args)

    try:
        simp_le = SimpLeCertGenerator(
            args.simp_le, args.document_root, args.testing)
        nginx_config = NginxConfigGenerator(
            args.templates, args.nginxconfd, args.document_root)
        vhosts = get_vhosts(args.vhostdir)
        rproxy = RProxy(simp_le, nginx_config, vhosts)
    except ConfigError as ce:
        logger.error(ce)  # pylint: disable=no-member
        sys.exit(1)
    rproxy.init_config()
    if args.mode == 'run':
        rproxy.run()


if __name__ == "__main__":
    main()
