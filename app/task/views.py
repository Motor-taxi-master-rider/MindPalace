from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from app.models import Category, DocumentCache, DocumentMeta, Permission, User
from app.task.forms import DocMetaForm

task = Blueprint('task', __name__)


@task.route('/doc_meta/my_documents', methods=['GET'])
@login_required
def get_my_doc_meta():
    """Get all documents meta data of user"""
    user = User.objects.get_or_404(id=current_user.id)
    documents = DocumentMeta.objects(create_by=user).all()
    return render_template(
        'task/document_dashboard.html',
        categories=Category,
        documents=documents)


@task.route('/doc_meta', methods=['GET', 'POST'])
@login_required
def new_doc_meta():
    """new document meta data for current user"""
    form = DocMetaForm()
    if form.validate_on_submit():
        print(form.category.data)
        doc_meta = DocumentMeta(
            theme=form.theme.data,
            category=form.category.data,
            url=form.link.data,
            priority=form.priority.data,
            create_by=current_user.id)
        doc_meta.save()
        flash(f'Document {str(doc_meta)} is successfully created.')
    return render_template('task/new_document.html', form=form)


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


@task.route('/doc_meta/delete/<string:doc_meta_id>', methods=['GET', 'POST'])
@login_required
def delete_doc_meta(doc_meta_id):
    """delete document meta data with given id"""
    doc_meta = DocumentMeta.objects.get_or_404(id=doc_meta_id)
    if current_user.can(
            Permission.ADMINISTER.value) or current_user == doc_meta.create_by:
        doc_meta.delete()
        flash(f'Document {str(doc_meta)} is successfully deleted.')
    else:
        abort(550)
    flash(f'Document {str(doc_meta.theme)} is successfully deleted.')
    return redirect(url_for('task.get_my_doc_meta'))
