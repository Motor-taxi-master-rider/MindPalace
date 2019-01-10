import os
from functools import partial

from fabric import task
from invoke.exceptions import ThreadException

from deploy.utils import DeployTask, logger


def _load_env_file():
    from pathlib import Path
    from dotenv import load_dotenv

    env_file = Path('.env-production')
    if not env_file.exists():
        env_file = Path('.env')

    load_dotenv(env_file)


@task
def setup_environment(conn):
    """Install and setup all base packages.

    This task should be executed once for the first time.
    """

    _load_env_file()

    task = DeployTask(conn)
    task.sudo('apt update')
    task.register_ssl_certification(os.environ['SSL_CERT_PATH'])

    system_packages = ('git', 'docker', ('ruby-sass', 'sass'), 'python3',
                       ('python3-pip', 'pip3'))
    for package in system_packages:
        if isinstance(package, tuple):
            package, executable = package
            apt_install = partial(task.apt_install, executable=executable)
        else:
            apt_install = task.apt_install

        try:
            apt_install(package)
        except ThreadException:
            logger.exception(f'Unable to install {package}.')
            return

    python_packages = ('docker-compose', )
    for package in python_packages:
        task.pip_install(package)


@task
def build_app(conn):
    """Build and start up application."""

    task = DeployTask(conn)
    task.fetch_repo()
    task.copy_env_file()
    task.start_app()
