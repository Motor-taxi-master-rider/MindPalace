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
        if not executable:
            executable = package

        if self.run(f'which {executable}', hide=True, warn=True).ok:
            version_info = self.run(
                f'{executable} --version', hide=True).stdout.strip()
            logger.info(f'{version_info} is already installed.')
        else:
            logger.info(f'Installing {package}......')
            self.sudo(f'apt install {package} -y', shell=False)

    def copy_env_file(self):
        project_path = dirname(realpath(join(__file__, pardir)))

        with self.cd(REPO_NAME):
            if self.exist(ENV_FILE):
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
            self.run(f'mv {env_file} {ENV_FILE}')

    def exist(self, path: str):
        return self.run(f'test -e "$(echo {path})"', hide=True, warn=True).ok

    def fetch_repo(self):
        if self.exist(REPO_NAME):
            with self.cd(REPO_NAME):
                self.run('git pull')
        else:
            self.run(f'git clone {GIT_LINK}')
            logger.info('Clone successfully.')

    def start_docker(self):
        with self.cd(REPO_NAME):
            self.sudo('docker-compose up')
