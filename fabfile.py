import os

from fabric import task

from deploy.utils import DeployTask


def _load_env_file():
    from os.path import exists
    from dotenv import load_dotenv

    env_file = '.env-production'
    if not exists(env_file):
        env_file = '.env'

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

    system_packages = ('git', 'docker', ('ruby-sass', 'sass'))
    for package in system_packages:
        if isinstance(package, tuple):
            package, executable = package
            task.apt_install(package, executable=executable)
        else:
            task.apt_install(package)

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
