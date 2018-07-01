from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, url_for)

from app.models import DocumentCache, DocumentMeta, Permission, User
from app.task.forms import DocMetaForm
from flask_login import current_user, login_required

task = Blueprint('task', __name__)


@task.route('/doc_meta/<string:user_id>/all', methods=['GET'])
@login_required
def get_all_doc_meta(user_id):
    """Get all documents meta data of user"""
    user = User.objects.get_or_404(id=user_id)
    documents = DocumentMeta.objects(create_by=user).all()
    return jsonify(documents)


@task.route('/doc_meta', methods=['POST'])
@login_required
def new_doc_meta():
    """new document meta data for current user"""
    form = DocMetaForm()
    if form.validate_on_submit():
        doc_meta = DocumentMeta(
            theme=form.theme.data,
            category=form.category.data,
            url=form.link.data,
            priority=form.priority.data,
            create_by=current_user)
        doc_meta.save()
        flash(f'Document {str(doc_meta)} is successfully created.')
    return 'success'


@task.route('/doc_meta/<string:doc_meta_id>', methods=['PUT'])
@login_required
def update_doc_meta(doc_meta_id):
    """update document meta data with given id"""
    doc_meta = DocumentMeta.objects.get(id=doc_meta_id)
    if doc_meta is None:
        abort(404)
    form = DocMetaForm()
    if form.validate_on_submit():
        doc_meta = DocumentMeta(
            theme=form.theme.data,
            category=form.category.data,
            url=form.link.data,
            priority=form.priority.data)
        doc_meta.save()
        flash(f'Document {str(doc_meta)} is successfully updated.')
    return 'success'


@task.route('/doc_meta/<string:doc_meta_id>', methods=['DELETE'])
@login_required
def delete_doc_meta(doc_meta_id):
    """delete document meta data with given id"""
    doc_meta = DocumentMeta.objects.get_or_404(id=doc_meta_id)
    if current_user.can(Permission.ADMINISTER) or current_user == doc_meta.create_by:
        doc_meta.delete()
        flash(f'Document {str(doc_meta)} is successfully deleted.')
    else:
        abort(550)
