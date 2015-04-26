from wtforms import Form, BooleanField, TextField, PasswordField, validators, StringField
from wtforms.fields.core import IntegerField


class BookForm(Form):
    course = StringField('Course ID', [validators.DataRequired()])
    book = StringField('Book Name', [validators.DataRequired()])
    author = StringField('Author Name', [validators.DataRequired()])
    edition = StringField('Edition', [validators.DataRequired()])
    price = IntegerField('Price', [validators.NumberRange(0), validators.DataRequired()])
    comments = StringField('Comments', [validators.Length(max=150)])
    ean = StringField("ean")
