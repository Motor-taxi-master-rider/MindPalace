from fabric import Config, Connection

from deploy.utils import DeployTask


def SetupEnvironment(conn: Connection):
    """Install and setup all base packages"""
    task = DeployTask(conn)
    task.sudo('apt update')

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


def BuildApp(conn: Connection):
    task = DeployTask(conn)
    task.fetch_repo()
    task.copy_env_file()
    task.start_app()


def main():
    config = Config(overrides={'sudo': {'password': '123'}})
    conn = Connection('192.168.226.130', config=config)
    BuildApp(conn)


if __name__ == '__main__':
    main()
