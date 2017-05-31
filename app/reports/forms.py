import datetime as datetime

from flask_wtf import Form
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields import (
    SelectField,
    StringField,
    SubmitField,
    IntegerField,
    TextAreaField,
    HiddenField,
    DateField,
    RadioField,
    FieldList,
    BooleanField
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

    car = BooleanField('Car', validators=[
        Optional()
    ])

    bus = BooleanField('Bus', validators=[
        Optional()
    ])

    truck = BooleanField('Truck', validators=[
        Optional()
    ])

    bicycle = BooleanField('Bicycle', validators=[
        Optional()
    ])

    pedestrian = BooleanField('Pedestrian', validators=[
        Optional()
    ])

    injuries = RadioField('Did an injury occur?', choices=[
        ('Yes', 'Yes'),
        ('No', 'No')
    ], validators=[InputRequired()])

    injuries_description = TextAreaField('Injuries Description', validators=[
        RequireDescription('injuries'),
        Length(max=5000)
    ])

    witness = RadioField('Did you observe or experience the incident?', choices=[
        ('Observed', 'Observed'),
        ('Experienced', 'Experienced')
    ], validators=[InputRequired()])

    category = SelectField('Category',
                choices=[("Failure to stop", "Failure to stop"),
                        ("Running a red light", "Running a red light"),
                        ("Swerving vehicle", "Swerving vehicle"),
                        ("Tailgating", "Tailgating"),
                        ("Cycling on sidewalk", "Cycling on sidewalk"),
                        ("Car door", "Car door"),
                        ("Crossing against signal", "Crossing against signal"),
                        ("Other", "Other")],
                validators=[
                    InputRequired()
                ])

    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=5000)
    ])

    road_conditions = TextAreaField('Weather/Road Conditions', validators=[
        Optional(),
        Length(max=5000)
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
