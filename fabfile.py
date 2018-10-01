from fabric import Config, Connection

from deploy.utils import DeployTask


def SetupEnvironment(conn: Connection):
    """Install and setup all base packages"""
    task = DeployTask(conn)
    packages = ('git', 'docker', 'docker-compose', ('ruby-sass', 'sass'))
    for package in packages:
        if isinstance(package, tuple):
            package, executable = package
            task.apt_install(package, executable=executable)
        else:
            task.apt_install(package)


def BuildApp(conn: Connection):
    task = DeployTask(conn)
    task.fetch_repo()
    task.copy_env_file()
    task.start_docker()


def main():
    config = Config(overrides={'sudo': {'password': '123'}})
    conn = Connection('192.168.226.130', config=config)
    BuildApp(conn)
    # SetupEnvironment(conn)


if __name__ == '__main__':
    main()
