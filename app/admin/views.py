from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import MessageQueue
from app.admin.forms import (ChangeAccountTypeForm, ChangeUserEmailForm,
                             InviteUserForm, NewUserForm)
from app.decorators import admin_required
from app.email import send_email
from app.models import EditableHTML, Role, User
from app.utils import get_queue

admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            password=form.password.data)
        user.save()
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(
            role=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data)
        user.save()
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue(MessageQueue.email.value).enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.objects().all()
    roles = Role.objects().all()
    return render_template(
        'admin/registered_users.html', users=users, roles=roles)


@admin.route('/user/<string:user_id>')
@admin.route('/user/<string:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.objects.get_or_404(id=user_id)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<string:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.objects.get_or_404(id=user_id)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        user.save()
        flash(
            'Email for user {} successfully changed to {}.'.format(
                user.full_name(), user.email), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route(
    '/user/<string:user_id>/change-account-type', methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if str(current_user.id) == user_id:
        flash(
            'You cannot change the type of your own account. Please ask '
            'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.objects.get_or_404(id=user_id)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        user.save()
        flash(
            'Role for user {} successfully changed to {}.'.format(
                user.full_name(), user.role.name), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<string:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.objects.get_or_404(id=user_id)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<string:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if str(current_user.id) == user_id:
        flash(
            'You cannot delete your own account. Please ask another '
            'administrator to do this.', 'error')
    else:
        user = User.objects.get(id=user_id)
        user.delete()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.objects(editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    editor_contents.save()

    return 'OK', 200
