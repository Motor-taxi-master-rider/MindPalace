#!/usr/bin/env python
import os

from flask_script import Manager, Shell
from redis import Redis
from rq import Connection, Queue, Worker

from app import create_app, db
from app.globals import MessageQueue
from app.models import DocumentCache, DocumentMeta, Role, User
from app.utils import generate_documents_for_user
from config import Config

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
    return dict(
        app=app,
        db=db,
        User=User,
        Role=Role,
        DocumentCache=DocumentCache,
        DocumentMeta=DocumentMeta)


manager.add_command('shell', Shell(make_context=make_shell_context))


@manager.command
def recreate_db():
    """
    Recreates a local database. You probably should not use this on
    production.
    """
    db.connection.drop_database(app.config['MONGODB_DB'])


@manager.option(
    '-n',
    '--number-users',
    default=10,
    type=int,
    help='Number of each model type to create',
    dest='number_users')
def add_fake_data(number_users):
    """
    Adds fake data to the database.
    """
    User.generate_fake(count=number_users)
    admin = User.objects(email=Config.ADMIN_EMAIL).first()
    generate_documents_for_user(admin)


@manager.command
def setup_dev():
    """Runs the set-up needed for local development."""
    setup_general()


@manager.command
def setup_prod():
    """Runs the set-up needed for production."""
    setup_general()


def setup_general():
    """Runs the set-up needed for both local development and production.
       Also sets up first admin user."""
    Role.insert_roles()
    admin_query = Role.objects(name='Administrator')
    if admin_query.first() is not None:
        admin = User.objects(email=Config.ADMIN_EMAIL).first()
        if not admin:
            admin = User(
                first_name='Admin',
                last_name='Account',
                password=Config.ADMIN_PASSWORD,
                confirmed=True,
                email=Config.ADMIN_EMAIL)
            admin.save()
            print('Added administrator {}'.format(admin.full_name()))

        for document in DocumentMeta.objects(create_by__exists=False).all():
            document.create_by = admin
            document.save()
        print('Assigned documents to {}'.format(admin.full_name()))


@manager.command
def run_worker():
    """Initializes a slim rq task queue."""
    listen = [queue.value for queue in MessageQueue]
    conn = Redis(
        host=app.config['RQ_HOST'],
        port=app.config['RQ_PORT'],
        db=app.config['RQ_DB'],
        password=app.config['RQ_PASSWORD'])

    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()


if __name__ == '__main__':
    manager.run()
