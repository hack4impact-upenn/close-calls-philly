import csv
import datetime
from ..decorators import admin_required
from datetime import datetime
from dateutil import parser
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


@admin.route('/upload_reports', methods=['POST'])
@login_required
@admin_required
def upload_reports():
    """Reads a csv and imports the data into a database."""
    # The indices in the csv of different data

    def parse_datetime(date_index, row):
        """for date_format in ['%m/%d/%Y %H:%M', '%m/%d/%y %H:%M']:
            try:
                time_1 = datetime.strptime(row[date_index], date_format)
            except ValueError:
                time_1 = None

            try:
                time_2 = datetime.strptime(row[date_index + 1],
                                          date_format)
            except ValueError:
                time_2 = None"""
        try:
            return parser.parse(row[date_index])
        except ValueError:
            return None

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
        print ('Row {:d}: {}L/'.format(row_number, error_message))

    witness_index = 0
    date_index = 1
    location_index = 2
    car_index = 3
    bus_index = 4
    truck_index = 5
    bicycle_index = 6
    pedestrian_index = 7
    injuries_index = 8
    injuries_desc_index = 9
    description_index = 10
    road_conditions_index = 11
    deaths_index = 12
    license_plates_index = 13
    picture_index = 14
    contact_name_index = 15
    contact_phone_index = 16
    contact_email_index = 17

    validator_form = IncidentReportForm()

    csv_file = request.files['file']
    try:
        csv_file.save(secure_filename(csv_file.filename))
        actual_file = open(csv_file.filename, 'r')
    except IOError:
        flash("The file could not be opened.", "error")
        return redirect(url_for('main.index'))
    with actual_file as csv_file:
        reader = csv.reader(csv_file)
        columns = next(reader)
        for c in range(len(columns)):
            columns[c] = columns[c].upper()
        if columns != ["DATE", "LOCATION", "NUMBER OF AUTOMOBILES", "NUMBER OF BICYCLES", "NUMBER OF PEDESTRIANS", "DESCRIPTION", "INJURIES", "INJURIES DESCRIPTION", "NUMBER OF DEATHS", "LICENSE PLATES", "PICTURE URL", "CONTACT NAME", "CONTACT PHONE", "CONTACT EMAIL"]:
            flash('The column names and order must match the specified form exactly. Please click the info icon for more details.', 'error')
            return redirect(url_for('main.index'))
        error_lines = []
        errors = []
        for i, row in enumerate(reader, start=2):  # i is the row number

            address_text = row[location_index]
            coords = geocode(address_text)

            # Ignore rows that do not have correct geocoding
            if coords[0] is None or coords[1] is None:
                print_error(i, 'Failed to geocode "{:s}"'.format(address_text))
                error_lines.append(i)

            # Insert correctly geocoded row to database
            else:
                loc = IncidentLocation(
                    latitude=coords[0],
                    longitude=coords[1],
                    original_user_text=address_text)
                db.session.add(loc)

                time = parse_datetime(date_index, row)
                if time is None:
                    error_lines.append(i)
                    errors.append("Date/Time Format")
                    continue

                witness_text = row[witness_index].strip()
                car_text = row[car_index].strip()
                bus_text = row[bus_index].strip()
                truck_text = row truck_index].strip()
                bicycle_text = row[bicycle_index].strip()
                pedestrian_text = row[pedestrian_index].strip()

                contact_name_text = row[contact_name_index].strip()
                contact_phone_text = row[contact_phone_index].strip()
                contact_email_text = row[contact_email_index].strip()

                # Validate all the fields
                validate_field = functools.partial(
                    validate_field_partial,
                    form=validator_form,
                    row_number=i
                )

                if not validate_field(
                    field=validator_form.description,
                    data=row[description_index]
                ):
                    error_lines.append(i)
                    errors.append("Description")

                if not validate_field(field=validator_form.picture_url,data=row[picture_index]):
                    error_lines.append(i)
                    errors.append("Picture URL")

                witness_text = trip_non_alphanumeric_chars(witness_text)
                car_text = strip_non_alphanumeric_chars(car_text)
                bus_text = strip_non_alphanumeric_chars(bus_text)
                truck_text = strip_non_alphanumeric_chars(truck_text)
                bicycle_text = strip_non_alphanumeric_chars(bicycle_text)
                pedestrian_text = strip_non_alphanumeric_chars(pedestrian_text)

                contact_name_text = strip_non_alphanumeric_chars(contact_name_text)
                contact_phone_text = strip_non_alphanumeric_chars(contact_phone_text)
                try:
                    incident = Incident(
                        witness=witness_text,
                        date=time,
                        address=loc,
                        car=bool(car_text) if len(car_text) > 0
                        else False,
                        bus=bool(car_text) if len(bus_text) > 0
                        else False,
                        truck=bool(car_text) if len(truck_text) > 0
                        else False,
                        bicycle=bool(car_text) if len(bicycle_text) > 0
                        else False,
                        pedestrian=bool(car_text) if len(pedestrian_text) > 0
                        else False,
                        injuries=row[injuries_index],
                        injuries_description=row[injuries_desc_index],
                        description=row[description_index],
                        road_conditions=row[road_conditions_index],
                        deaths=int(row[deaths_index]) if len(row[deaths_index]) > 0 else 0,
                        license_plates=row[license_plates_index],
                        picture_url=row[picture_index],
                        contact_name=contact_name_text if len(contact_name_text) > 0
                        else None,
                        contact_phone=int(contact_phone_text) if len(contact_phone_text) > 0
                        else None,
                        contact_email=contact_email_text if len(contact_email_text) > 0
                        else None,
                    )
                    db.session.add(incident)
                except Exception:
                    error_lines.append(i)
                    errors.append("Other")

        db.session.commit()
        if len(error_lines) > 0:
            flash_str = 'We found errors in the following lines:\n'
            for l, e in zip(error_lines, errors):
                flash_str += "Line: " + str(l) + ', Error: ' + e + '\n'
            flash(flash_str, 'error')
        else:
            flash('All lines were added successfully.', 'success')
        return redirect(url_for('main.index'))
