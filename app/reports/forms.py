import datetime as datetime

from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (
    StringField,
    SubmitField,
    IntegerField,
    TextAreaField,
    HiddenField,
    DateField,
    RadioField,
    FieldList
)
from wtforms_components import TimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import (
    InputRequired,
    Length,
    Optional,
    NumberRange,
    URL,
    Regexp
)

from app.custom_validators import StrippedLength, ValidLocation, RequiredIf, RequireDescription
from .. import db


class IncidentReportForm(Form):

    address = StringField('Address', validators=[
        InputRequired('Address is required.'),
        ValidLocation()
        ])

    latitude = HiddenField('Latitude')

    longitude = HiddenField('Longitude')

    automobile_num = IntegerField('Number of Automobiles', validators=[
        InputRequired()
    ])

    bicycle_num = IntegerField('Number of Bicycles', validators=[
        InputRequired()
    ])

    pedestrian_num = IntegerField('Number of Pedestrians', validators=[
        InputRequired()
    ])

    today = datetime.datetime.today()

    date = DateField('Date of Event (year-month-day)',
                     default=today.strftime('%m-%d-%Y'),
                     validators=[InputRequired()])

    time = TimeField('Time of Event (hours:minutes am/pm)',
                     default=today.strftime('%I:%M %p'),
                     validators=[InputRequired()])

    picture_file = FileField(
        'Upload a Photo',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp'],
                        'Only images are allowed.')
        ]
    )

    picture_url = StringField('Picture URL', validators=[
                Optional(),
                URL(message='Picture URL must be a valid URL. '
                    'Please upload the image to an image hosting website '
                    'and paste the link here.')
        ])

    description = TextAreaField('Description', validators=[
        InputRequired(),
        Length(max=5000)
    ])

    injuries = RadioField('Did an injury occur?', choices=[
        ('Yes', 'Yes'),
        ('No', 'No')
    ], validators=[InputRequired()])

    injuries_description = TextAreaField('Injuries Description', validators=[
        RequireDescription('injuries'),
        Length(max=5000)
    ])

    deaths = IntegerField('Number of Deaths', validators=[Optional()])

    license_plates = TextAreaField('License Plates', validators=[
        Optional(),
        Length(max=5000)
    ])

    contact_name = StringField('Contact Name', validators=[
        Optional(),
        Length(max=1000)
    ])

    contact_phone = StringField('Contact Phone', validators=[
        Optional(),
        Length(max=1000)
    ])

    contact_email = StringField('Contact E-mail', validators=[
        Optional(),
        Length(max=100)
    ])

    submit = SubmitField('Create Report')


class EditIncidentReportForm(IncidentReportForm):

    submit = SubmitField('Update Report')
