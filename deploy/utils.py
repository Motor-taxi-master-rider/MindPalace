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

        if not self.executable_exist(executable):
            logger.info(f'Installing {package}......')
            if package == 'docker':
                self._install_docker()
                self._register_docker_mirror()
            else:
                self.sudo(f'apt install {package} -y')

    def copy_env_file(self):
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

    def append_content(self, content: str, path: str):
        self.sudo(f'bash -c "echo \'{content}\' >> {path}"')

    def executable_exist(self, executable: str):
        result = self.run(f'which {executable}', hide=True, warn=True).ok
        if result:
            version_info = self.run(
                f'{executable} --version', hide=True).stdout.strip()
            logger.info(f'{version_info} is already installed.')
        return result

    def fetch_repo(self):
        if self.remote_exists(REPO_NAME):
            with self.cd(REPO_NAME):
                self.run('git pull')
        else:
            self.run(f'git clone {GIT_LINK}')
            logger.info('Clone successfully.')

    def pip_install(self, package: str):
        if not self.executable_exist(package):
            logger.info(f'Installing {package}......')
            self.sudo(f'pip install {package}')

    def remote_exists(self, path: str):
        return self.run(f'test -e "$(echo {path})"', hide=True, warn=True).ok

    def start_app(self):
        """Start the docker compose.

        Currently this is a workaround for `cd` and `sudo` interaction in fabric 2.4.0.
        Trace the issue https://github.com/pyinvoke/invoke/issues/459 to
        get more bug detail.
        TODO: move the workaround after the bug fix
        """

        self.sudo(f'bash -c "cd {REPO_NAME} && docker-compose up -d"')

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
            self.append_content(mirror_info, docker_mirror_file)
