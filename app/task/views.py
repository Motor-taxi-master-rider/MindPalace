from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from mongoengine.errors import NotUniqueError

from app.models import Category, DocumentMeta, Permission, User
from app.task.forms import DocMetaForm

task = Blueprint('task', __name__)


@task.route('/doc_meta/my_documents')
@login_required
def my_doc_meta():
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
        doc_meta = DocumentMeta(
            theme=form.theme.data,
            category=form.category.data,
            url=form.url.data,
            priority=form.priority.data,
            create_by=current_user.id
        )
        doc_meta.save()
        flash(f'Document {str(doc_meta)} is successfully created.',
              'form-success')
    return render_template(
        'task/manage_document.html',
        form=form,
        action='Create',
        data_type='New Document')


@task.route('/doc_meta/<string:doc_meta_id>', methods=['GET', 'POST'])
@login_required
def update_doc_meta(doc_meta_id):
    """update document meta data with given id"""
    doc_meta = DocumentMeta.objects.get_or_404(id=doc_meta_id)
    form = DocMetaForm(obj=doc_meta)
    if form.validate_on_submit():
        doc_meta.theme = form.theme.data
        doc_meta.category = form.category.data
        doc_meta.url = form.url.data
        doc_meta.priority = form.priority.data
        doc_meta.save()
        flash(f'Document {str(doc_meta)} is successfully updated.',
              'form-success')
    return render_template(
        'task/manage_document.html',
        form=form,
        action='Update',
        data_type=str(doc_meta))


@task.route('/doc_meta/delete/<string:doc_meta_id>', methods=['GET', 'POST'])
@login_required
def delete_doc_meta(doc_meta_id):
    """delete document meta data with given id"""
    doc_meta = DocumentMeta.objects.get_or_404(id=doc_meta_id)
    if current_user.can(
            Permission.ADMINISTER.value) or current_user == doc_meta.create_by:
        doc_meta.delete()
    else:
        abort(401)
    flash(f'Document {str(doc_meta.theme)} is successfully deleted.',
          'form-success')
    return redirect(url_for('task.my_doc_meta'))
