from .. import db


class EditableHTML(db.Document):  # type: ignore
    editor_name = db.StringField(max_length=100, unique=True)
    value = db.StringField()

    @staticmethod
    def get_editable_html(editor_name):
        editable_html_obj = EditableHTML.objects(
            editor_name=editor_name).first()

        if editable_html_obj is None:
            editable_html_obj = EditableHTML(editor_name=editor_name, value='')
        return editable_html_obj
