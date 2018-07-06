#!/usr/bin/env python
"""
autovenv -- helper script for pip and venv

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import hashlib
import logging
import os
import os.path
import subprocess
import sys
import venv

logger = logging.getLogger(__name__)


class PipHelper:
    """
    Helper Class to run pip commands in the venv
    """

    def __init__(self, python_exe):
        """
        :param python_exe: path to the venv or the python exe in the venv
        """
        if os.path.isdir(python_exe):
            if sys.platform == 'win32':
                binname = 'Scripts'
            else:
                binname = 'bin'
            binpath = os.path.join(os.path.abspath(python_exe), binname)
            if sys.platform == 'darwin' and \
                    '__PYVENV_LAUNCHER__' in os.environ:
                executable = os.environ['__PYVENV_LAUNCHER__']
            else:
                executable = sys.executable
            _, exename = os.path.split(os.path.abspath(executable))
            python_exe = os.path.join(binpath, exename)
        self.pip_cmd = [python_exe, '-Im', 'pip']

    def install(self, *params):
        """
        Calls pip install with the given parameters.

        :param params: List of parameters
        """
        return subprocess.check_call(
            self.pip_cmd + ['install'] +  list(params))

    def freeze(self, freeze_filepath):
        """
        Calls pip freeze and stores the output under the given filepath.

        :param freeze_filepath: Path to store the freeze output
        """
        with open(freeze_filepath, mode='w', newline='\n') as freeze_file:
            # Using check_output for line ending conversion to \n
            output = subprocess.check_output(
                self.pip_cmd + ['freeze'],
                universal_newlines=True)
            freeze_file.write(output)

    def download(self, download_folder, *params):
        """
        Calls pip download and stores all requirements in the given folder.

        :param download_folder: Path to the download folder
        """
        return subprocess.check_call(
            self.pip_cmd + ['download', '-d', download_folder] + list(params))


def checksum_of_file(filepath):
    """
    Creates a checksum of the given filepath.

    :params filepath: Path to the file
    """
    with open(filepath, mode='rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
        logger.debug("Checksum of %s was %s", filepath, checksum)
        return checksum


class AutoEnvException(Exception):
    """ Base Exception for AuteEnv """

    def __init__(self, message):
        """
        :params message: Message that desribes the error
        """
        self.message = message
        super().__init__(message)


class AutoEnvBuilder(venv.EnvBuilder):
    """
    EnvBuilder that automatically installs all dependencies from
    the requirements.txt
    """

    CHECKSUM_FILENAME = 'requirements.sha256'
    REQUIREMENTS_FILENAME = 'requirements.txt'
    FREEZE_FILENAME = 'requirements.freeze'
    DOWNLOAD_FOLDER = 'requirements'

    def __init__(self, use_index=None, update_pip=False,
                 update_setuptools=False, symlinks=False):
        self.use_index = use_index
        self.update_pip = update_pip
        self.update_setuptools = update_setuptools
        super().__init__(
            system_site_packages=False, clear=True,
            symlinks=False, upgrade=False, with_pip=True)

    def _freeze(self, pip):
        filepath = os.path.abspath(self.FREEZE_FILENAME)
        logger.info('Creating freeze file: %s', filepath)
        pip.freeze(filepath)

    def download(self, env_dir):
        """
        Downloads all requirements into the download folder.
        """
        if not self._is_frozen():
            raise AutoEnvException(
                "VENV is not frozen! Run setup before download.")
        pip = PipHelper(env_dir)
        pip.download(self.DOWNLOAD_FOLDER, '-r', self.FREEZE_FILENAME)

    def create(self, env_dir):
        if not self._check_venv(env_dir):
            logger.info('Recreating venv.')
            super().create(env_dir)

    def _check_venv(self, env_dir):
        if not os.path.isdir(env_dir):
            logger.info('No venv found.')
            return False
        if not self._is_frozen():
            logger.info('Venv not frozen.')
            return False
        logger.info('Checking current venv.')
        checksum_filepath = os.path.join(env_dir, self.CHECKSUM_FILENAME)
        if not os.path.isfile(checksum_filepath):
            logger.info('No checksum file found.')
            return False
        with open(checksum_filepath, mode='r') as f:
            checksum = f.read()
        if checksum != checksum_of_file(self.FREEZE_FILENAME):
            logger.info('Invalid checksum found.')
            return False
        logger.info('Venv is up to date.')
        return True

    def post_setup(self, context):
        """
        Set up any packages which need to be pre-installed into the
        environment being created.
        :param context: The information for the environment creation request
                        being processed.
        """
        os.environ['VIRTUAL_ENV'] = context.env_dir
        pip = PipHelper(context.env_exe)
        if self.update_setuptools:
            logger.info('Updateing setuptools ...')
            pip.install('-U', 'setuptools')
        if self.update_pip:
            logger.info('Updateing pip ...')
            pip.install('-U', 'pip')
        self._install_requirements(pip)
        if not self._is_frozen():
            self._freeze(pip)
        self._create_checksum_file(context)

    def _get_requirements_files_parameters(self):
        if self._is_frozen():
            logger.info('Using freeze file: %s', self.FREEZE_FILENAME)
            return ['-r', self.FREEZE_FILENAME]
        logger.info("Using requirements file: %s",
                    self.REQUIREMENTS_FILENAME)
        return ['-r', self.REQUIREMENTS_FILENAME]

    def _install_requirements(self, pip):
        logger.info('Running pip install ...')
        cmd = self._get_requirements_files_parameters()
        # Checking requirements folder
        if os.path.isdir('requirements'):
            cmd.extend(['-f', 'requirements'])
        # setting no-index
        if self.use_index is False:
            cmd.append('--no-index')
        pip.install(*cmd)

    def _create_checksum_file(self, context):
        logger.info('Creating checksum of %s ...', self.FREEZE_FILENAME)
        checksum = checksum_of_file(self.FREEZE_FILENAME)
        checksum_filepath = os.path.join(
            context.env_dir, self.CHECKSUM_FILENAME)
        with open(checksum_filepath, mode='w') as f:
            f.write(checksum)

    def _is_frozen(self):
        return os.path.isfile(self.FREEZE_FILENAME)

def main(args=None):
    """ Main function """
    # Setup argparse.
    import argparse
    parser = argparse.ArgumentParser(
        prog=__name__ if __name__ != '__main__' else 'autovenv.py',
        description="Creates a virtual Python environment with all"
                    "dependencies from the requirements.txt installed.")
    parser.add_argument(
        '--update-setuptools',
        default=False, action='store_true', dest='update_setuptools',
        help='Updates setuptools in the environment.')
    parser.add_argument(
        '--update-pip',
        default=False, action='store_true', dest='update_pip',
        help='Updates pip in the environment.')
    parser.add_argument(
        '--symlinks',
        default=False, action='store_true', dest='symlinks',
        help='Try to use symlinks rather than copies, when symlinks are not '
             'the default for the platform.')
    venv_path_basedir = '.'
    venv_path = os.path.join(venv_path_basedir, 'venv')
    parser.add_argument('-p', '--path', dest='venv_path', default=venv_path,
                        help="Sets the path to the venv.")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="increase output verbosity")
    parser.add_argument(
        '--no-index', action='store_false', dest='use_index', default=True,
        help='Force disable pip index.')
    parser.add_argument(
        'mode', choices=['setup', 'download'],
        default='setup', nargs='?',
        help="Use 'setup' to create the venv.\n"
             "Use 'download' to download all requirements into a folder "
             "('./requirements').")

    # Parse the arguments
    options = parser.parse_args(args)

    # Setup Logger
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    if options.verbosity:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    # add console_handler to logger
    logger.addHandler(console_handler)

    # Run AutoEnvBuilder
    builder = AutoEnvBuilder(update_pip=options.update_pip,
                             update_setuptools=options.update_setuptools,
                             symlinks=options.symlinks)
    try:
        if options.mode == 'download':
            builder.download(options.venv_path)
        else:
            builder.create(options.venv_path)
    except AutoEnvException as autoenv_exception:
        logger.error(autoenv_exception.message)
if __name__ == '__main__':
    main()
