import logging
import sys
from os.path import dirname, exists, join, pardir, realpath

from fabric.connection import Connection

REPO_NAME = 'MindPalace'
GIT_LINK = f'https://github.com/Motor-taxi-master-rider/{REPO_NAME}.git'
ENV_FILE, ENV_FILE_PRODUCTION = '.env', '.env-production'

logger = logging.getLogger('deploy')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)


class DeployException(Exception):
    pass


class DeployTask:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def __getattr__(self, item):
        if item in ('run', 'sudo', 'put', 'cd'):
            return getattr(self._conn, item)
        raise NotImplemented(item)

    def apt_install(self, package: str, executable=None):
        """Use apt-get to install packages in ubuntu.

        Some packages may have a different executable name from the package name(e.g. ruby-sass),
         then `executable` should be set.
        """

        if not executable:
            executable = package

        if not self.executable_exist(executable):
            logger.info(f'Installing {package}......')
            if package == 'docker':
                self._install_docker()
                self._register_docker_mirror()
            else:
                self.sudo(f'apt install {package} -y')

    def copy_env_file(self):
        """Copy project environment file to remote server.

        '.env-production' file will be chosen to copy prior to '.env' to ease the local development.
        """

        project_path = dirname(realpath(join(__file__, pardir)))

        with self.cd(REPO_NAME):
            if self.remote_exists(ENV_FILE):
                return

            if exists(join(project_path, ENV_FILE_PRODUCTION)):
                env_file = ENV_FILE_PRODUCTION
                logger.info(
                    f'Copy {ENV_FILE_PRODUCTION} to {self._conn.host}.')
            elif exists(join(project_path, ENV_FILE)):
                env_file = ENV_FILE
                logger.info(
                    f'Copy {ENV_FILE_PRODUCTION} to {self._conn.host}.')
            else:
                logger.error(f'No env file found in {project_path}.')
                return

            self.put(env_file, remote=f'{REPO_NAME}/')
            # rename .env-production to .env
            self.run(f'mv {env_file} {ENV_FILE}')

    def copy_content(self, content: str, path: str):
        """Add content to remote server file, new file will be create if not exists"""

        self.sudo(f'bash -c "echo \'{content}\' >> {path}"')

    def executable_exist(self, executable: str):
        """Check whether a executable binary is ready."""

        result = self.run(f'which {executable}', hide=True, warn=True).ok
        if result:
            version_info = self.run(
                f'{executable} --version', hide=True).stdout.strip()
            logger.info(f'{version_info} is already installed.')
        return result

    def fetch_repo(self):
        """Sync git repository on remote server.

        Repository will be cloned from remote for the first time. `pull` procedure will be execute to
        get further update.
        """

        if self.remote_exists(REPO_NAME):
            with self.cd(REPO_NAME):
                self.run('git pull')
        else:
            self.run(f'git clone {GIT_LINK}')
            logger.info('Clone successfully.')

    def pip_install(self, package: str):
        """Use pip to install python package on remote server."""

        logger.info(f'Installing {package}......')
        self.sudo(f'pip3 install {package}')

    def remote_exists(self, path: str):
        """Check whether a file or directory exists on remote server."""

        return self.run(f'test -e "$(echo {path})"', hide=True, warn=True).ok

    def register_ssl_certification(self, path: str):
        """User openssl to create ssl certification file."""

        if self.remote_exists(f'{path}/key.pem') or self.remote_exists(
                f'{path}/cert.pem'):
            logger.info('Ssl certification file is already existed in {path}.')
            return

        if not self.remote_exists(path):
            self.run(f'mkdir {path}')
        self.sudo(
            f'openssl req -x509 -newkey rsa:4096 -days 365 -nodes -keyout {path}/key.pem -out {path}/cert.pem',
            pty=True)

    def start_app(self):
        """Start the docker compose.

        Currently this is a workaround for `cd` and `sudo` interaction in fabric 2.4.0.
        Trace the issue https://github.com/pyinvoke/invoke/issues/459 to
        get more bug detail.
        TODO: move the workaround after the bug fix
        """

        self.sudo(
            f'bash -c "cd {REPO_NAME} && docker-compose pull &&docker-compose down && docker-compose up -d"'
        )

    def _install_docker(self):
        """Special process to install docker.

        See：https://docs.docker.com/install/linux/docker-ce/ubuntu/#set-up-the-repository
        """

        dependencies = ('apt-transport-https', 'ca-certificates', 'curl',
                        'software-properties-common')
        self.sudo(f'apt install {" ".join(dependencies)} -y')
        self.sudo(
            'bash -c "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -"',
            hide=True)
        self.sudo('apt-key fingerprint 0EBFCD88', hide=True)
        self.sudo(
            'add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"',
            hide=True)
        self.sudo('apt update')
        self.sudo('apt install docker-ce -y')

    def _register_docker_mirror(self):
        mirror_info = '{"registry-mirrors": ["https://registry.docker-cn.com"]}'
        docker_mirror_file = '/etc/docker/daemon.json'
        if not self.remote_exists(docker_mirror_file):
            logger.info('Registering docker mirror...')
            self.copy_content(mirror_info, docker_mirror_file)
