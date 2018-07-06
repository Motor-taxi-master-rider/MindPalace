from flask import Blueprint, abort, flash, redirect, render_template, url_for
from mongoengine.errors import NotUniqueError

from app.models import Category, DocumentMeta, Permission, User
from app.task.forms import DocMetaForm
from flask_login import current_user, login_required

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
        try:
            doc_meta.save()
        except NotUniqueError:
            flash('Theme already exists.','form-error')
        else:
            flash(f'Document {str(doc_meta)} is successfully created.', 'form-success')
            return redirect(url_for('task.new_doc_meta'))
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
        flash(f'Document {str(doc_meta)} is successfully updated.', 'form-success')
    return 'success'


@task.route('/doc_meta/delete/<string:doc_meta_id>', methods=['GET', 'POST'])
@login_required
def delete_doc_meta(doc_meta_id):
    """delete document meta data with given id"""
    doc_meta = DocumentMeta.objects.get_or_404(id=doc_meta_id)
    if current_user.can(
            Permission.ADMINISTER.value) or current_user == doc_meta.create_by:
        doc_meta.delete()
    else:
        abort(550)
    flash(f'Document {str(doc_meta.theme)} is successfully deleted.', 'form-success')
    return redirect(url_for('task.get_my_doc_meta'))
