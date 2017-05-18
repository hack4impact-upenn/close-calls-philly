import pytz
import traceback
import enum

from datetime import datetime, timedelta
from enum import Enum
from flask import current_app
from flask_rq import get_queue
from .. import db
from . import User
from ..email import send_email
from ..utils import get_current_weather, url_for_external
from sqlalchemy.dialects.postgresql import ENUM


class IncidentLocation(db.Model):
    __tablename__ = 'incident_locations'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    # TODO: ensure original_user_text is always non-null
    original_user_text = db.Column(db.Text)  # the raw text which we geocoded
    incident_id = db.Column(db.Integer,
                                   db.ForeignKey('incidents.id'))

    def __repr__(self):
        return str(self.original_user_text)

class Incident(db.Model):
    __tablename__ = 'incidents'

    id = db.Column(db.Integer, primary_key=True)
    address = db.relationship('IncidentLocation',
                                uselist=False,
                                lazy='joined',
                                backref='incident')
    date = db.Column(db.DateTime)
    car = db.Column(db.Boolean)
    bus = db.Column(db.Boolean)
    truck = db.Column(db.Boolean)
    bicycle = db.Column(db.Boolean)
    pedestrian = db.Column(db.Boolean)
    description = db.Column(db.Text)
    license_plates = db.Column(db.String, default=None) # optional
    injuries = db.Column(db.Text)
    injuries_description = db.Column(db.Text, default=None) # optional
    deaths = db.Column(db.Integer, default=0) # optional
    picture_url = db.Column(db.Text, default=None) # optional
    contact_name = db.Column(db.Text, default=None) # optional
    contact_phone = db.Column(db.Integer, default=None) #optional
    contact_email = db.Column(db.Text, default=None) #optional
    picture_deletehash = db.Column(db.Text, default=None)

    def __init__(self, **kwargs):
        super(Incident, self).__init__(**kwargs)

        if self.date is None:
            self.date = datetime.now(pytz.timezone(
                current_app.config['TIMEZONE']))
            self.date = self.date.replace(tzinfo=None)

        self.description = self.description.replace('\n', ' ').strip()
        self.description = self.description.replace('\r', ' ').strip()

    @staticmethod
    def generate_fake(count=100, **kwargs):
        """Generate a number of fake reports for testing."""
        from sqlalchemy.exc import IntegrityError
        from random import seed, choice, randint
        from datetime import timedelta
        from faker import Faker
        import random
        import string

        def flip_coin():
            """Returns True or False with equal probability"""
            return choice([True, False])

        def rand_alphanumeric(n):
            """Returns random string of alphanumeric characters of length n"""
            r = ''.join(random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(n))
            return r

        fake = Faker()

        seed()
        for i in range(count):
            l = IncidentLocation(
                original_user_text=fake.address(),
                latitude=str(fake.geo_coordinate(center=39.951021,
                                                 radius=0.01)),
                longitude=str(fake.geo_coordinate(center=-75.197243,
                                                  radius=0.01))
            )
            has_injury = 'No'
            injuries_description_entry = ""
            if random.random() >= 0.5:
                has_injury = 'Yes'
                injuries_description_entry = "An injury occurred."
            license_plates_str = ""
            license_plates_str += rand_alphanumeric(6)
            r = Incident(
                address=l,
                date=fake.date_time_between(start_date="-1y", end_date="now"),
                car=bool(random.getrandbits(1)),
                bus=bool(random.getrandbits(1)),
                truck=bool(random.getrandbits(1)),
                bicycle=bool(random.getrandbits(1)),
                pedestrian=bool(random.getrandbits(1)),
                description=fake.paragraph(),
                injuries=has_injury,
                injuries_description=injuries_description_entry,
                deaths=choice([0]*98+[0, 1]),
                license_plates=license_plates_str,
                picture_url=fake.image_url(),
                contact_name = "Test Contact",
                contact_phone=1234567890,
                contact_email = fake.email(),
                **kwargs
            )
            db.session.add(r)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
