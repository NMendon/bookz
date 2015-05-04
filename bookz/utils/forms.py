from wtforms import Form, BooleanField, TextField, PasswordField, validators, StringField
from wtforms.fields.core import IntegerField, DecimalField


class BookForm(Form):
    course = StringField('Course ID', [validators.DataRequired()])
    book = StringField('Book Name', [validators.DataRequired()])
    author = StringField('Author Name', [validators.DataRequired()])
    edition = StringField('Edition', [validators.DataRequired()])
    price = DecimalField('Price', [
        validators.NumberRange(0, message="Must be an >= 0")])
    comments = StringField('Comments', [validators.Length(max=150)])
    ean = StringField("ean")

class BuyerForm(Form):
    course = StringField('Course ID', [validators.DataRequired()])
    book = StringField('Book Name')
    author = StringField('Author Name')
    edition = StringField('Edition',)
    price = DecimalField('Price')
    comments = StringField('Comments', [validators.Length(max=150)])
    ean = StringField("ean")
