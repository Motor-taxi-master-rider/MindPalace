from app.models import Role, User
from flask_mongoengine.wtf.fields import ModelSelectField
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.fields import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import Email, EqualTo, InputRequired, Length


class ChangeUserEmailForm(FlaskForm):
    email = EmailField(
        'New email', validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.objects(email=field.data).first():
            raise ValidationError('Email already registered.')


class ChangeAccountTypeForm(FlaskForm):
    role = ModelSelectField('New account type', validators=[InputRequired()], model=Role, label_attr='name')
    submit = SubmitField('Update role')


class InviteUserForm(FlaskForm):
    role = ModelSelectField('Account type', validators=[InputRequired()], model=Role, label_attr='name')
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.objects(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')
