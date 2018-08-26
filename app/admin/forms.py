from flask import url_for
from flask_mongoengine.wtf.fields import ModelSelectField
from flask_wtf import FlaskForm
from wtforms.fields import PasswordField, StringField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import (Email, EqualTo, InputRequired, Length,
                                ValidationError)

from app.models import Role, User


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
    role = ModelSelectField(
        'New account type',
        validators=[InputRequired()],
        model=Role,
        label_attr='name')
    submit = SubmitField('Update role')


class InviteUserForm(FlaskForm):
    role = ModelSelectField(
        'Account type',
        validators=[InputRequired()],
        model=Role,
        label_attr='name')
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
        user = User.objects(email=field.data).first()

        if not user:
            return True

        if user.confirmed:
            raise ValidationError('Email already registered.')
        else:
            # user is invited but not confirmed
            from app.jobs.send_email import send_email
            token = user.generate_confirmation_token()
            invite_link = url_for(
                'account.join_from_invite',
                user_id=user.id,
                token=token,
                _external=True)
            send_email.queue(
                recipient=user.email,
                subject='You Are Invited To Join',
                template='account/email/invite',
                user=user,
                invite_link=invite_link,
            )
            raise ValidationError(
                'Email is not confirmed, verification will resend to user.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')
