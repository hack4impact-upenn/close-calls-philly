import csv
import pytz

from datetime import date, timedelta, datetime

from flask import render_template, current_app, flash, Response
from werkzeug import secure_filename

from . import main
from app import models, db
from app.reports.forms import IncidentReportForm
from app.models import Incident, EditableHTML
from app.utils import upload_image, geocode


@main.route('/', methods=['GET', 'POST'])
@main.route('/map', methods=['GET', 'POST'])
def index():
    form = IncidentReportForm()

    if form.validate_on_submit():

        # If geocode happened client-side, it's not necessary to geocode again.
        lat, lng = form.latitude.data, form.longitude.data
        if not lat or not lng:
            lat, lng = geocode(form.location.data)

        l = models.Location(original_user_text=form.location.data,
                            latitude=lat,
                            longitude=lng)

        new_incident = models.IncidentReport(
            vehicle_id=form.vehicle_id.data,
            license_plate=form.license_plate.data,
            location=l,
            date=datetime.combine(form.date.data, form.time.data),
            duration=timedelta(minutes=form.duration.data),
            description=form.description.data,
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

@main.route('/download_reports', methods=['GET'])
def download_reports():
    """Download a csv file of all incident reports visible on the map."""

    def encode(s):
        return s.encode('utf-8') if s else ''

    current_date = str(date.today())
    csv_name = 'IncidentReports-' + current_date + '.csv'
    outfile = open(csv_name, 'w+')
    print('initial file contents:', outfile.read())

    wr = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    reports = db.session.query(IncidentReport).all()
    wr.writerow(['DATE', 'LOCATION', 'VEHICLE ID', 'DURATION',
                'LICENSE PLATE', 'DESCRIPTION'])
    for r in reports:
        wr.writerow([r.date, r.location,
                     r.vehicle_id, r.duration,
                     r.license_plate, encode(r.description)])

    endfile = open(csv_name, 'r+')
    data = endfile.read()
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=" + csv_name})
