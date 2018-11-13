from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user, login_required
from flask_mongoengine.pagination import Pagination
from mongoengine.errors import NotUniqueError

from app.globals import ALL_CATEGORY, DOCUMENT_PER_PAGE
from app.models import Category, DocumentMeta, Permission
from app.task.forms import DocMetaForm
from app.task.utils import MY_DOC_PIPELINE

task = Blueprint('task', __name__)


@task.route('/doc_meta/my_documents')
@login_required
def my_doc_meta():
    """Get all documents meta data of user"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get(
        'category', Category.SHORT_TERM.value, type=str)
    search = request.args.get('search', None)
    filter = {'create_by': current_user.id}

    if category != ALL_CATEGORY:
        filter['category'] = category

    documents = DocumentMeta.objects(**filter).exclude('cache')

    if search:
        documents = documents.search_text(search)
        documents = documents.order_by('$text_score')
    else:
        documents = list(documents.aggregate(*MY_DOC_PIPELINE))
    documents = Pagination(documents, page=page, per_page=DOCUMENT_PER_PAGE)
    return render_template(
        'task/document_dashboard.html',
        current_category=category,
        current_search=search,
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
            tags=form.tags.data,
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
            doc_meta.tags = form.tags.data
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
    return {
        'categories': [c.value for c in Category],
        'all_category': ALL_CATEGORY
    }
