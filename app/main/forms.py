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
    RadioField
)
from wtforms_components import TimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import (
    InputRequired,
    Length,
    Optional,
    NumberRange,
    URL,
    Regexp,
    Required
)

from app.custom_validators import StrippedLength, ValidLocation, RequiredIf
from .. import db


class RequiredIf(Required):
    # a validator which makes a field required if
    # another field is set and has a truthy value

    def __init__(self, other_field_name, *args, **kwargs):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if (other_field.data):
            super(RequiredIf, self).__call__(form, field)


class IncidentReportForm(Form):
    location = StringField('Address', validators=[
        InputRequired('Address is required.'),
        ValidLocation()
        ])

    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')

    automobile_num = IntegerField('Number of Automobiles', validators=[
        Optional()
    ])

    bicycle_num = IntegerField('Number of Bicycles', validators=[
        Optional()
    ])

    pedestrian_num = IntegerField('Number of Pedestrians', validators=[
        Optional()
    ])

    today = datetime.datetime.today()

    date = DateField('Date (year-month-day)',
                     default=today.strftime('%m-%d-%Y'),
                     validators=[InputRequired()])

    time = TimeField('Time (hours:minutes am/pm)',
                     default=today.strftime('%I:%M %p'),
                     validators=[InputRequired()])

    picture_file = FileField(
        'Upload a photo (optional)',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpe', 'jpeg', 'png', 'gif', 'svg', 'bmp'],
                        'Only images are allowed.')
        ]
    )

    description = TextAreaField('Description', validators=[
        InputRequired(),
        Length(max=5000)
    ])

    injuries = RadioField(
        'Did an injury occur?',
        coerce=bool,
        choices=[(True, 'Yes'), (False, 'No')]
    )

    injuries_description = TextAreaField('Injuries Description', validators=[
        RequiredIf('injuries'),
        Length(max=5000)
    ])

    contact_name = StringField('Contact Name (optional)', validators=[
        Optional(),
        Length(max=1000)
    ])

    contact_phone = StringField('Contact Phone (optional)', validators=[
        Optional(),
        Length(max=1000)
    ])

    contact_email = StringField('Contact E-mail (optional)', validators=[
        Optional(),
        Length(max=100)
    ])

    submit = SubmitField('Create Report')


class EditIncidentReportForm(IncidentReportForm):
    duration = StringField('Idling Duration (h:m:s)', validators=[
        InputRequired('Idling duration is required.'),
        Regexp(r'^(\d{1,2}:)(\d{1,2}:)(\d{1,2})$',
               message='Write duration as HH:MM:SS')
    ])

    submit = SubmitField('Update Report')
