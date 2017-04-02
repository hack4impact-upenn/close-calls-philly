import csv
import functools
from datetime import datetime
from app.utils import geocode, strip_non_alphanumeric_chars
from app.models import Location, IncidentReport
from app.reports.forms import IncidentReportForm

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


def parse_to_db(db, filename):
    """Reads a csv and imports the data into a database."""
    # The indices in the csv of different data
    
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

    with open(filename, 'r') as csv_file:
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
                loc = Location(
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


