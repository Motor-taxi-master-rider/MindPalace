from flask import current_app
from flask_login import AnonymousUserMixin, UserMixin
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db, login_manager


class Permission:
    GENERAL = 0x01
    ADMINISTER = 0xff


class Role(db.Document):
    name = db.StringField(max_length=64, unique=True)
    index = db.StringField(max_length=64)
    default = db.BooleanField(default=False)
    permissions = db.IntField()
    meta = {'collection': 'roles', 'indexes': [{'fields': ['default']}]}

    @staticmethod
    def insert_roles():
        roles = {
            'User': (Permission.GENERAL, 'main', True),
            'Administrator': (
                Permission.ADMINISTER,
                'admin',
                False  # grants all permissions
            )
        }
        for r in roles:
            role = Role.objects(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.index = roles[r][1]
            role.default = roles[r][2]
            role.save()

    def __repr__(self):
        return '<Role \'%s\'>' % self.name


class User(UserMixin, db.DynamicDocument):
    confirmed = db.BooleanField(default=False)
    first_name = db.StringField(max_length=64)
    last_name = db.StringField(max_length=64)
    email = db.StringField(max_length=64, unique=True)
    password_hash = db.StringField(max_length=128)
    role = db.ReferenceField(Role)
    meta = {
        'collection':
        'users',
        'indexes': [{
            'fields': ['first_name']
        }, {
            'fields': ['last_name']
        }, {
            'fields': ['email']
        }]
    }

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        if self.role is None:
            if self.email == current_app.config['ADMIN_EMAIL']:
                self.role = Role.objects(
                    permissions=Permission.ADMINISTER).first()
            if self.role is None:
                self.role = Role.objects(default=True).first()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def can(self, permissions):
        return self.role is not None and \
            (self.role.permissions & permissions) == permissions

    def is_admin(self):
        return self.can(Permission.ADMINISTER)

    @property
    def password(self):
        raise AttributeError('`password` is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=604800):
        """Generate a confirmation token to email a new user."""

        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': str(self.id)})

    def generate_email_change_token(self, new_email, expiration=3600):
        """Generate an email change token to email an existing user."""
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': str(self.id), 'new_email': new_email})

    def generate_password_reset_token(self, expiration=3600):
        """
        Generate a password reset change token to email to an existing user.
        """
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': str(self.id)})

    def confirm_account(self, token):
        """Verify that the provided token is for this user's id."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('confirm') != str(self.id):
            return False
        self.confirmed = True
        self.save()
        return True

    def change_email(self, token):
        """Verify the new email for this user."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('change_email') != str(self.id):
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.objects(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.save()
        return True

    def reset_password(self, token, new_password):
        """Verify the new password for this user."""
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (BadSignature, SignatureExpired):
            return False
        if data.get('reset') != str(self.id):
            return False
        self.password = new_password
        self.save()
        return True

    @staticmethod
    def generate_fake(count=100, **kwargs):
        """Generate a number of fake users for testing."""
        from random import seed, choice
        from faker import Faker

        fake = Faker()
        roles = Role.objects().all()

        seed()
        for i in range(count):
            u = User(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                password='password',
                confirmed=True,
                role=choice(roles),
                **kwargs)
            u.save()

    def __repr__(self):
        return '<User \'%s\'>' % self.full_name()


class AnonymousUser(AnonymousUserMixin):
    def can(self, _):
        return False

    def is_admin(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.objects(id=str(user_id))
