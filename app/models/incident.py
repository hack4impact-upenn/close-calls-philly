from datetime import datetime, timedelta
from flask import current_app
from flask.ext.rq import get_queue
from .. import db

class Location(db.Model):
    __tablename__ = 'locations'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.String(50))
    longitude = db.Column(db.String(50))
    # TODO: ensure original_user_text is always non-null
    original_user_text = db.Column(db.Text)  # the raw text which we geocoded
    incident_report_id = db.Column(db.Integer,
                                   db.ForeignKey('incident_reports.id'))

    def __repr__(self):
        return str(self.original_user_text)

class IncidentType(enum.Enum):
    PEDESTRIAN = "Pedestrian"
    BICYCLE = "Bicycle"
    AUTOMOBILE = "Automobile"
    OTHER = "Other"        

class Incident(db.Model):
    __tablename__ = 'incidents'
    id = db.Column(db.Integer, primary_key=True)
    location = db.relationship('Location',
                                uselist=False,
                                lazy='joined',
                                backref='incident')
    date = db.Column(db.DateTime)
    incident_type = db.Column(enum.Enum(Incidenttype))
    description = db.Column(db.Text)
    injuries = db.Column(db.Text)
    picture_url = db.Column(db.Text, default=None) # optional
    comments = db.Column(db.Text, default=None) # optional
    contact_phone = db.Column(db.Integer, default=None) #optional
    contact_email = db.Column(db.Text, default=None) #optional

