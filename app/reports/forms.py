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
)

from app.custom_validators import StrippedLength, ValidLocation, RequiredIf
from ..models import Agency
from .. import db


class IncidentReportForm(Form):
    address = StringField('Address', validators=[
        InputRequired('Address is required.'),
        ValidLocation()
        ])

    automobile_num = IntegerField('Automobile', validators=[
        Optional()
    ])

    bicycle_num = IntegerField('Bicycle', validators=[
        Optional()
    ])

    motorcycle_num = IntegerField('Motorcycle', validators=[
        Optional()
    ])

    pedestrian_num = IntegerField('Pedestrian', validators=[
        Optional()
    ])

    other_num = IntegerField('Other', validators=[
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

    description = TextAreaField('Additional Notes', validators=[
        InputRequired(),
        Length(max=5000)
    ])

    injuries = TextAreaField('Injuries (optional)', validators=[
        Optional(),
        Length(max=5000)
    ])

    contact_name = StringField('Contact Name (optional): only visible to administrator', validators=[
        Optional(),
        Length(max=1000)
    ])    

    submit = SubmitField('Create Report')


class EditIncidentReportForm(IncidentReportForm):
    duration = StringField('Idling Duration (h:m:s)', validators=[
        InputRequired('Idling duration is required.'),
        Regexp(r'^(\d{1,2}:)(\d{1,2}:)(\d{1,2})$',
               message='Write duration as HH:MM:SS')
    ])

    # All agencies should be options in the EditForm but only official agencies
    # should be an option in the ReportForm
    agency = QuerySelectField(
        'Vehicle Agency ',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Agency),
        allow_blank=True,
        blank_text='Other',
    )

    submit = SubmitField('Update Report')
