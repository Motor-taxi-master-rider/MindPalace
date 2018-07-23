from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from mongoengine.errors import NotUniqueError

from app.models import Category, DocumentMeta, Permission
from app.task.forms import DocMetaForm

DOCUMENT_PER_PAGE = 10
ALL_CATEGORY = 'All categories'

task = Blueprint('task', __name__)


@task.route('/doc_meta/my_documents')
@login_required
def my_doc_meta():
    """Get all documents meta data of user"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', ALL_CATEGORY, type=str)
    if category == ALL_CATEGORY:
        documents = DocumentMeta.objects(create_by=current_user.id)
    else:
        documents = DocumentMeta.objects(
            create_by=current_user.id, category=Category[category].value)
    documents = documents.order_by('-priority', '-update_at').paginate(
        page=page, per_page=DOCUMENT_PER_PAGE)
    return render_template(
        'task/document_dashboard.html',
        current_category=category,
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
            create_by=current_user.id)
        try:
            doc_meta.save()
        except NotUniqueError:
            flash('Theme already exists.', 'form-error')
        else:
            flash(f'Document {str(doc_meta)} is successfully created.',
                  'form-success')
        return redirect(url_for('task.new_doc_meta'))
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
        try:
            doc_meta.theme = form.theme.data
            doc_meta.category = form.category.data
            doc_meta.url = form.url.data
            doc_meta.priority = form.priority.data
            doc_meta.save()
        except NotUniqueError:
            flash('Theme already exists.', 'form-error')
        else:
            flash(f'Document {str(doc_meta)} is successfully updated.',
                  'form-success')
        return redirect(
            url_for('task.update_doc_meta', doc_meta_id=doc_meta_id))
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


@task.context_processor
def inject_template_global():
    return {'categories': Category, 'all_category': ALL_CATEGORY}
