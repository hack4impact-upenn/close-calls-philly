import datetime
from flask_wtf import Form
from wtforms.fields import (
    StringField,
    SubmitField,
    IntegerField,
    TextAreaField,
    HiddenField,
    DateField,
    FileField
)
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import (
    InputRequired,
    Length,
    Optional,
    NumberRange,
    URL
)
from app.custom_validators import StrippedLength
from .. import db


class IncidentReportForm(Form):
    vehicle_id = StringField('Vehicle ID', validators=[
        InputRequired('Vehicle ID is required.'),
        StrippedLength(
            min_length=2,
            max_length=15,
            message='Vehicle ID must be between 2 to 15 characters after '
                    'removing all non-alphanumeric characters.'
        ),
    ])

    license_plate = StringField('License Plate Number', validators=[
        Optional(),
        StrippedLength(
            min_length=4,
            max_length=8,
            message='License plate must be between 4 to 8 characters after '
                    'removing all non-alphanumeric characters.'
        )
    ])

    bus_number = IntegerField('Bus Number', validators=[
        Optional()
    ])

    led_screen_number = IntegerField('LED Screen Number', validators=[
        Optional()
    ])

    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    location = StringField('Address')
    today = datetime.date.today()
    date = DateField('Date', default=today,
                     validators=[Optional()])

    # TODO - add support for h:m:s format
    duration = IntegerField('Idling Duration (minutes)', validators=[
        InputRequired('Idling duration (minutes) is required.'),
        NumberRange(min=0,
                    max=10000,
                    message='Idling duration must be between '
                            '0 and 10000 minutes.')
    ])

    picture_file = FileField('Upload a picture of the idling vehicle.',
                             validators=[Optional()])

    picture_url = StringField('Picture URL', validators=[
        Optional(),
        URL(message='Picture URL must be a valid URL. '
                    'Please upload the image to an image hosting website '
                    'and paste the link here.')
        ])

    description = TextAreaField('Additional Notes', validators=[
        Optional(),
        Length(max=5000)
    ])

    submit = SubmitField('Create Report')
