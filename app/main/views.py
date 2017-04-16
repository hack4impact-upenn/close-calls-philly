import csv
import pytz

from datetime import date, timedelta, datetime

from flask import render_template, current_app, flash, Response, redirect, url_for
from werkzeug import secure_filename

from . import main
from app import models, db
from app.reports.forms import IncidentReportForm
from app.models import Incident, IncidentLocation, EditableHTML
from app.utils import upload_image, geocode


@main.route('/', methods=['GET', 'POST'])

@main.route('/map', methods=['GET', 'POST'])
def index():
    form = IncidentReportForm()

    if form.validate_on_submit():

        # If geocode happened client-side, it's not necessary to geocode again.
        lat, lng = form.latitude.data, form.longitude.data
        if not lat or not lng:
            lat, lng = geocode(form.address.data)

        l = IncidentLocation(original_user_text=form.address.data,
                            latitude=lat,
                            longitude=lng)

        new_incident = Incident(
            address=l,
            date=datetime.combine(form.date.data, form.time.data),
            pedestrian_num=form.pedestrian_num.data,
            bicycle_num=form.bicycle_num.data,
            automobile_num=form.automobile_num.data,
            description=form.description.data,
            injuries=form.injuries.data,
            injuries_description=form.injuries_description.data,
            license_plates=form.license_plates.data.upper(),
            contact_name=form.contact_name.data,
            contact_phone=form.contact_phone.data,
            contact_email=form.contact_email.data
        )

        if form.picture_file.data.filename:
            filepath = secure_filename(form.picture_file.data.filename)
            form.picture_file.data.save(filepath)

            # synchronously upload image because heroku resets the file system
            # after the request
            link, deletehash = upload_image(
                imgur_client_id=current_app.config['IMGUR_CLIENT_ID'],
                imgur_client_secret=current_app.config['IMGUR_CLIENT_SECRET'],
                app_name=current_app.config['APP_NAME'],
                image_file_path=filepath
            )

            new_incident.picture_url = link
            new_incident.picture_deletehash = deletehash

        db.session.add(new_incident)
        db.session.commit()
        flash('Report successfully submitted.', 'success')
        return redirect(url_for('main.index'))

    # pre-populate form
    form.date.default = datetime.now(pytz.timezone(
        current_app.config['TIMEZONE']))
    form.time.default = datetime.now(pytz.timezone(
        current_app.config['TIMEZONE']))
    form.process()

    return render_template('main/map.html',
                           form=form,
                           incident_reports=Incident.query.all())


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template('main/about.html',
                           editable_html_obj=editable_html_obj)


@main.route('/faq')
def faq():
    editable_html_obj = EditableHTML.get_editable_html('faq')
    return render_template('main/faq.html',
                           editable_html_obj=editable_html_obj)
