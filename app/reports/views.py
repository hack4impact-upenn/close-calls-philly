from datetime import datetime

from flask import render_template, abort, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from flask_rq import get_queue
from werkzeug import secure_filename

from .forms import EditIncidentReportForm

from . import reports
from .. import db
from ..models import Incident
from ..decorators import admin_required
from ..utils import (
    flash_errors,
    geocode,
    parse_timedelta,
    delete_image,
    upload_image,
)


@reports.route('/all')
@login_required
@admin_required
def view_reports():
    """View all idling incident reports.
    Admins can see all reports.
    General users do not have access to this page."""

    if current_user.is_admin():
        incident_reports = Incident.query.all()

    # TODO test using real data
    return render_template('reports/reports.html', reports=incident_reports)

@reports.route('/<int:report_id>')
@reports.route('/<int:report_id>/info')
@login_required
def report_info(report_id):
    """View a report"""
    report = Incident.query.filter_by(id=report_id).first()

    if report is None:
        abort(404)

    # Either the user is looking at their own report, or the user is an admin.
    if not current_user.is_admin():
        abort(403)

    return render_template('reports/manage_report.html', report=report)


@reports.route('/<int:report_id>/edit_info', methods=['GET', 'POST'])
@login_required
def edit_report_info(report_id):
    """Change the fields for a report"""
    report = Incident.query.filter_by(id=report_id).first()

    if report is None:
        abort(404)
    # Either the user is editing their own report, or the user is an admin.
    if not current_user.is_admin():
        abort(403)

    form = EditIncidentReportForm()

    if form.validate_on_submit():

        report.car = form.car.data
        report.bus = form.bus.data
        report.truck = form.truck.data
        report.bicycle = form.bicycle.data
        report.pedestrian = form.pedestrian.data

        lat, lng = geocode(form.address.data)
        report.address.latitude, report.address.longitude = lat, lng
        report.address.original_user_text = form.address.data

        d, t = form.date.data, form.time.data
        report.date = datetime(year=d.year, month=d.month, day=d.day,
                               hour=t.hour, minute=t.minute, second=t.second)

        report.picture_url = form.picture_url.data
        report.category = form.category.data
        report.description = form.description.data
        report.injuries = form.injuries.data
        report.injuries_description = form.injuries_description.data
        report.witness = form.witness.data
        report.road_conditions = form.road_conditions.data
        report.deaths = form.deaths.data
        if (form.deaths.data == None):
            report.deaths = 0
        report.license_plates = form.license_plates.data.upper()

        if form.picture_file.data.filename:
            filepath = secure_filename(form.picture_file.data.filename)
            form.picture_file.data.save(filepath)

            # synchronously upload image so that the user will be able to see
            # the changes immediately.
            link, deletehash = upload_image(
                imgur_client_id=current_app.config['IMGUR_CLIENT_ID'],
                imgur_client_secret=current_app.config['IMGUR_CLIENT_SECRET'],
                app_name=current_app.config['APP_NAME'],
                image_file_path=filepath
            )

            report.picture_url = link
            report.picture_deletehash = deletehash

        report.contact_name = form.contact_name.data
        report.contact_phone = form.contact_phone.data
        report.contact_email = form.contact_email.data

        db.session.add(report)
        db.session.commit()
        flash('Report information updated.', 'form-success')
    elif form.errors.items():
        flash_errors(form)

    # pre-populate form

    form.car.default = report.car
    form.bus.default = report.bus
    form.truck.default = report.truck
    form.bicycle.default = report.bicycle
    form.pedestrian.default = report.pedestrian

    form.address.default = report.address.original_user_text

    form.date.default = report.date
    form.time.default = report.date

    form.picture_url.default = report.picture_url
    form.category.default = report.category
    form.description.default = report.description
    form.injuries.default = report.injuries
    form.injuries_description.default = report.injuries_description
    form.deaths.default = report.deaths
    form.license_plates.default = report.license_plates
    form.contact_name.default = report.contact_name
    form.contact_phone.default = report.contact_phone
    form.contact_email.default = report.contact_email


    form.process()

    return render_template('reports/manage_report.html', report=report,
                           form=form)


@reports.route('/<int:report_id>/delete')
@login_required
def delete_report_request(report_id):
    """Request deletion of a report."""
    report = Incident.query.filter_by(id=report_id).first()

    if report is None:
        abort(404)

    if not current_user.is_admin():
        abort(403)

    return render_template('reports/manage_report.html', report=report)


@reports.route('/<int:report_id>/_delete')
@login_required
def delete_report(report_id):
    """Delete a report"""

    report = Incident.query.filter_by(id=report_id).first()

    if report.picture_deletehash:
        # Asynchronously delete the report's image
        get_queue().enqueue(
            delete_image,
            deletehash=report.picture_deletehash,
            imgur_client_id=current_app.config['IMGUR_CLIENT_ID'],
            imgur_client_secret=current_app.config['IMGUR_CLIENT_SECRET'],
        )
    # report_user_id = report.user_id

    db.session.delete(report)
    db.session.commit()
    flash('Successfully deleted report.', 'success')

    # TODO - address edge case where an admin clicks on their own report from
    # reports/all endpoint, should redirect back to /all. use cookies
    # if report_user_id == current_user.id:
    #     return redirect(url_for('reports.view_my_reports'))
    # else:
    return redirect(url_for('reports.view_reports'))
