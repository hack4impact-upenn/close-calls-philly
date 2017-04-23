import csv
import datetime
from ..decorators import admin_required
from datetime import datetime
from flask import (
    render_template,
    abort,
    redirect,
    flash,
    url_for,
    request,
    Response,
)
from flask_login import login_required, current_user
from flask_wtf import CsrfProtect
from flask_rq import get_queue
import functools
from werkzeug.utils import secure_filename
from .forms import (
    ChangeUserEmailForm,
    ChangeUserPhoneNumberForm,
    ChangeAccountTypeForm,
    InviteUserForm,
)
from . import admin
from ..models import User, Role, EditableHTML, Incident, IncidentLocation
from ..reports.forms import IncidentReportForm

from .. import db
from ..utils import parse_phone_number, url_for_external, geocode, strip_non_alphanumeric_chars

from ..email import send_email


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    return render_template('admin/index.html')


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User(role=form.role.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    email=form.email.data,
                    phone_number=parse_phone_number(form.phone_number.data))

        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        invite_link = url_for_external('account.join_from_invite',
                                       user_id=user.id, token=token)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
        return redirect(url_for('admin.invite_user'))
    return render_template('admin/invite_user.html', form=form)


@admin.route('/users')
@login_required
@admin_required
def registered_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template('admin/registered_users.html', users=users,
                           roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/change-email', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_email(user_id):
    """Change a user's email."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserEmailForm()
    if form.validate_on_submit():
        user.email = form.email.data
        db.session.add(user)
        db.session.commit()
        flash('Email for user {} successfully changed to {}.'
              .format(user.full_name(), user.email),
              'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/change-phone-number',
             methods=['GET', 'POST'])
@login_required
@admin_required
def change_user_phone_number(user_id):
    """Change a user's phone number."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    form = ChangeUserPhoneNumberForm()
    if form.validate_on_submit():
        user.phone_number = parse_phone_number(form.phone_number.data)
        db.session.add(user)
        db.session.commit()
        flash('Phone number for user {} successfully changed to {}.'
              .format(user.full_name(), user.phone_number),
              'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/change-account-type',
             methods=['GET', 'POST'])
@login_required
@admin_required
def change_account_type(user_id):
    """Change a user's account type."""
    if current_user.id == user_id:
        flash('You cannot change the type of your own account. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = ChangeAccountTypeForm()
    if form.validate_on_submit():
        user.role = form.role.data
        db.session.add(user)
        db.session.commit()
        flash('Role for user {} successfully changed to {}.'
              .format(user.full_name(), user.role.name),
              'form-success')
    form.role.default = user.role
    form.process()
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.registered_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.get_editable_html(editor_name)
    editor_contents.value = edit_data

    db.session.add(editor_contents)
    db.session.commit()

    return 'OK', 200


@admin.route('/download_reports', methods=['GET'])
@login_required
@admin_required
def download_reports():
    """Download a csv file of all incident reports."""

    def encode(s):
        return s.encode('utf-8') if s else ''

    current_date = str(datetime.date.today())
    csv_name = 'IncidentReports-' + current_date + '.csv'
    outfile = open(csv_name, 'w+')
    print('initial file contents:', outfile.read())

    wr = csv.writer(outfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    reports = db.session.query(Incident).all()
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

@admin.route('/upload_reports', methods=['POST'])
@login_required
@admin_required
def upload_reports():
    """Reads a csv and imports the data into a database."""
    # The indices in the csv of different data
    
    def parse_start_end_time(date_index, row):
        for date_format in ['%m/%d/%Y %H:%M', '%m/%d/%y %H:%M']:
            try:
                time_1 = datetime.strptime(row[date_index], date_format)
            except ValueError:
                time_1 = None

            try:
                time_2 = datetime.strptime(row[date_index + 1],
                                          date_format)
            except ValueError:
                time_2 = None

        return time_1, time_2


    def validate_field_partial(field, data, form, row_number):
        """TODO: docstring"""
        field.data = data
        field.raw_data = data
        validated = field.validate(form)

        if not validated:
            for error in field.errors:
                print_error(row_number, error)

        return validated


    def print_error(row_number, error_message):
        """TODO: docstring"""
        print ('Row {:d}: {}'.format(row_number, error_message))

    date_index = 0
    location_index = 1
    description_index = 6
    injuries_index = 7
    pedestrian_num_index = 2
    bicycle_num_index = 4
    automobile_num_index = 3
    other_num_index = 5
    picture_index = 8
    contact_name_index = 9
    contact_phone_index = 10
    contact_email_index = 11
    
    validator_form = IncidentReportForm()

    csv_file = request.files['file']
    csv_file.save(secure_filename(csv_file.filename))

    with open(csv_file.filename, 'r') as csv_file:
        reader = csv.reader(csv_file)
        # columns = reader.next()

        for i, row in enumerate(reader, start=2):  # i is the row number

            address_text = row[location_index]
            coords = geocode(address_text)

            # Ignore rows that do not have correct geocoding
            if coords[0] is None or coords[1] is None:
                print_error(i, 'Failed to geocode "{:s}"'.format(address_text))

            # Insert correctly geocoded row to database
            else:
                loc = IncidentLocation(
                    latitude=coords[0],
                    longitude=coords[1],
                    original_user_text=address_text)
                db.session.add(loc)

                time1, time2 = parse_start_end_time(date_index, row)

                pedestrian_num_text = row[pedestrian_num_index].strip()
                bicycle_num_text = row[bicycle_num_index].strip()
                automobile_num_text = row[automobile_num_index].strip()
                other_num_text = row[other_num_index].strip()

                contact_name_text = row[contact_name_index].strip()
                contact_phone_text = row[contact_phone_index].strip()
                contact_email_text = row[contact_email_index].strip()

                # Validate all the fields
                validate_field = functools.partial(
                    validate_field_partial,
                    form=validator_form,
                    row_number=i
                )

                errors = 0

                if not validate_field(
                    field=validator_form.description,
                    data=row[description_index]
                ):
                    errors += 1

                if not validate_field(
                    field=validator_form.picture_url,
                    data=row[picture_index]
                ):
                    errors += 1

                if errors == 0:
                    pedestrian_num_text = strip_non_alphanumeric_chars(pedestrian_num_text)
                    bicycle_num_text = strip_non_alphanumeric_chars(bicycle_num_index)
                    automobile_num_text = strip_non_alphanumeric_chars(automobile_num_index)
                    other_num_text = strip_non_alphanumeric_chars(other_num_index)

                    contact_name_text = strip_non_alphanumeric_chars(contact_name_index)
                    contact_phone_text = strip_non_alphanumeric_chars(contact_phone_index)
                    contact_email_text = strip_non_alphanumeric_chars(contact_email_index)

                    incident = Incident(
                        date=time1,
                        pedestrian_num=int(pedestrian_num_text) if len(pedestrian_num_text) > 0
                        else 0,
                        bicycle_num=int(bicycle_num_text) if len(bicycle_num_text) > 0
                        else 0,
                        automobile_num=int(automobile_num_text) if len(automobile_num_text) > 0
                        else 0,
                        other_num=int(other_num_text) if len(other_num_text) > 0
                        else 0,
                        description=row[description_index],
                        injuries=row[injuries_index],
                        picture_url=row[picture_index],
                        contact_name=contact_name_text if len(contact_name_text) > 0
                        else None,
                        contact_phone=int(contact_phone_text) if len(contact_phone_text) > 0
                        else None,
                        contact_email=contact_email_text if len(contact_email_text) > 0
                        else None,
                    )
                    db.session.add(incident)

        db.session.commit()
        return columns
