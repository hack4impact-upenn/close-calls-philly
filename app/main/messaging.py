import string
import itertools
from flask import request, make_response, current_app
from flask_rq import get_queue
from . import main
from .. import db
from ..utils import (
    geocode,
    upload_image,
    get_rq_scheduler,
    attach_image_to_incident_report,
    url_for_external
)
from ..models import User
from ..reports.forms import IncidentReportForm
from datetime import datetime, timedelta
import twilio.twiml
from twilio.rest import TwilioRestClient


STEP_INIT = 0
STEP_LOCATION = 1
STEP_LICENSE_PLATE = 2
STEP_VEHICLE_ID = 3
STEP_DURATION = 4
STEP_DESCRIPTION = 5
STEP_PICTURE = 6


@main.route('/report_incident', methods=['GET'])  # noqa
def handle_message():
    """Called by Twilio when a text message is received."""
    body = str(request.values.get('Body')).lower().strip()
    num_media = int(request.values.get('NumMedia'))
    twilio_hosted_media_url = str(request.values.get('MediaUrl0')) \
        if num_media > 0 else None
    message_sid = str(request.values.get('MessageSid'))
    phone_number = str(request.values.get('From'))

    twiml = twilio.twiml.Response()

    # Retrieve incident cookies
    step = int(request.cookies.get('messagecount', 0))
    vehicle_id = str(request.cookies.get('vehicle_id', ''))
    license_plate = str(request.cookies.get('license_plate', ''))
    duration = int(request.cookies.get('duration', 0))
    description = str(request.cookies.get('description', ''))
    location = str(request.cookies.get('location', ''))
    picture_url = str(request.cookies.get('picture_url', ''))

    if 'report' == body.lower():
        # reset report variables/cookies
        vehicle_id = ''
        license_plate = ''
        duration = 0
        description = ''
        location = ''
        picture_url = ''

        step = handle_start_report(twiml)

    elif step == STEP_LOCATION:
        location, step = handle_location_step(body, step, twiml)

    elif step == STEP_LICENSE_PLATE:
        license_plate, step = handle_license_plate_step(body, step, twiml)

    elif step == STEP_VEHICLE_ID:
        vehicle_id, step = handle_vehicle_id_step(body, step, twiml)

    elif step == STEP_DURATION:
        duration, step = handle_duration_step(body, step, twiml)

    elif step == STEP_DESCRIPTION:
        description, step = handle_description_step(body, step, twiml)

    elif step == STEP_PICTURE:
        step, image_job_id = handle_picture_step(step, message_sid,
                                                 twilio_hosted_media_url)

        new_incident = handle_create_report(description, duration,
                                            license_plate, location,
                                            picture_url, vehicle_id,
                                            phone_number)

        twiml.message('Thanks! See your report on the map at {}'
                      .format(url_for_external('main.index')))

        if new_incident.user is None:
            twiml.message('Want to keep track of all your reports? Create an '
                          'account at {}'
                          .format(url_for_external('account.register')))
        else:
            twiml.message('See all your reports at {}'
                          .format(url_for_external('reports.view_my_reports')))

        if image_job_id is not None:
            get_queue().enqueue(
                attach_image_to_incident_report,
                depends_on=image_job_id,
                incident_report=new_incident,
                image_job_id=image_job_id,
            )

        # reset report variables/cookies
        step = STEP_INIT

    else:
        twiml.message('Welcome to {}! Please reply "report" to report an '
                      'idling incident.'
                      .format(current_app.config['APP_NAME']))

    response = make_response(str(twiml))

    set_cookie(response, 'messagecount', str(step))
    set_cookie(response, 'vehicle_id', vehicle_id)
    set_cookie(response, 'license_plate', license_plate)
    set_cookie(response, 'duration', str(duration))
    set_cookie(response, 'description', description)
    set_cookie(response, 'location', location)
    set_cookie(response, 'picture_url', picture_url)

    return response


def handle_start_report(twiml):
    """Handle a message from the user indicating they want to start a new
    report."""
    step = STEP_LOCATION
    twiml.message('What is your location? Be specific! (e.g. "34th and '
                  'Spruce in Philadelphia PA")')
    return step


def handle_location_step(body, step, twiml):
    """Handle a message from the user containing the report's location."""
    validator_form = IncidentReportForm()
    errors = data_errors(form=validator_form, field=validator_form.location,
                         data=body)

    if len(errors) == 0:
        location = body
        step = STEP_LICENSE_PLATE
        twiml.message('What is the license plate number? Reply "no" to skip. '
                      '(e.g. MG1234E)')
    else:
        location = ''
        reply_with_errors(errors, twiml, 'location')

    return location, step


def handle_license_plate_step(body, step, twiml):
    """Handle a message from the user containing the report's license plate."""
    if body.lower() == 'no':
        body = ''

    validator_form = IncidentReportForm()
    errors = data_errors(
        form=validator_form,
        field=validator_form.license_plate,
        data=body
    )
    if len(errors) == 0:
        license_plate = body
        step = STEP_VEHICLE_ID
        twiml.message('What is the Vehicle ID? This is usually on the back or '
                      'side of the vehicle. (e.g. 105014)')
    else:
        license_plate = ''
        reply_with_errors(errors, twiml, 'license plate')

    return license_plate, step


def handle_vehicle_id_step(body, step, twiml):
    """Handle a message from the user containing the report's vehicle id."""
    validator_form = IncidentReportForm()
    errors = data_errors(form=validator_form, field=validator_form.vehicle_id,
                         data=body)

    if len(errors) == 0:
        vehicle_id = body
        step = STEP_DURATION
        twiml.message('How many minutes have you observed the vehicle idling? '
                      '(e.g. 10)')
    else:
        vehicle_id = ''
        reply_with_errors(errors, twiml, 'vehicle ID')

    return vehicle_id, step


def handle_duration_step(body, step, twiml):
    """Handle a message from the user containing the report's duration."""
    errors = []
    try:
        body = int(body)
    except ValueError:
        errors.append('Please enter a valid integer.')

    if len(errors) == 0:
        duration = body
        step = STEP_DESCRIPTION
        twiml.message('Please describe the situation (e.g. The driver is '
                      'sleeping)')
    else:
        duration = 0
        reply_with_errors(errors, twiml, 'duration')

    return duration, step


def handle_description_step(body, step, twiml):
    """Handle a message from the user containing the report's description."""
    validator_form = IncidentReportForm()
    errors = data_errors(form=validator_form, field=validator_form.description,
                         data=body)

    if len(errors) == 0:
        description = body
        step = STEP_PICTURE
        twiml.message('Last, can you take a photo of the vehicle and text '
                      'it back? Reply "no" to skip.')
    else:
        description = ''
        reply_with_errors(errors, twiml, 'description')

    return description, step


def handle_picture_step(step, message_sid, twilio_hosted_media_url):
    """Handle a message from the user containing the report's picture."""
    image_job_id = None
    if twilio_hosted_media_url is not None:
        account_sid = current_app.config['TWILIO_ACCOUNT_SID']
        auth_token = current_app.config['TWILIO_AUTH_TOKEN']

        image_job_id = get_queue().enqueue(
            upload_image,
            imgur_client_id=current_app.config['IMGUR_CLIENT_ID'],
            imgur_client_secret=current_app.config['IMGUR_CLIENT_SECRET'],
            app_name=current_app.config['APP_NAME'],
            image_url=twilio_hosted_media_url
        ).id

        get_rq_scheduler().enqueue_in(
            timedelta(minutes=10),
            delete_mms,
            account_sid=account_sid,
            auth_token=auth_token,
            message_sid=message_sid
        )

    return step, image_job_id


def reply_with_errors(errors, twiml, field_name):
    """Reply to the user with errors in a field."""
    twiml.message('Sorry, there were some errors with your response. '
                  'Please enter the {} again.'.format(field_name))
    twiml.message('Errors:\n{}'.format('\n'.join(errors)))


def delete_mms(account_sid, auth_token, message_sid):
    """Deletes the media attached to the given message from Twilio."""
    client = TwilioRestClient(account_sid, auth_token)
    for media in client.messages.get(message_sid).media_list.list():
        media.delete()


def all_strings(max_count):
    """Makes a alphabetical list from a to z and then continues with
    letter combinations. Modified from
    http://stackoverflow.com/questions/29351492/how-to-make-a-continuous-alphabetic-list-python-from-a-z-then-from-aa-ab-ac-e"""  # noqa
    repeat_size = 1
    count = 0
    ret = []
    while True:
        for s in itertools.product(string.ascii_uppercase, repeat=repeat_size):
            count += 1
            if count > max_count:
                return ret
            ret.append(''.join(s))
        repeat_size += 1


def set_cookie(resp, key, val, expiration=1):
    """Sets a expiring cookie in the response."""
    expires = datetime.utcnow() + timedelta(hours=expiration)
    expires_str = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    resp.set_cookie(key, value=val, expires=expires_str)


def data_errors(field, data, form):
    """Return errors in given data using a WTForm field."""
    field.data = data
    field.raw_data = data
    validated = field.validate(form)

    if not validated:
        return field.errors

    return []
