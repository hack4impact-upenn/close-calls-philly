import unittest
import datetime
from app import create_app, db
from app.models import Incident, IncidentLocation, Agency, User


class IncidentTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_location_no_incident(self):
        loc = IncidentLocation(
            latitude='39.951039',
            longitude='-75.197428',
            original_user_text='3700 Spruce St.'
        )
        self.assertTrue(loc.latitude == '39.951039')
        self.assertTrue(loc.longitude == '-75.197428')
        self.assertTrue(loc.original_user_text == '3700 Spruce St.')
        self.assertTrue(loc.incident_report is None)

    def test_location_has_incident(self):
        incident_report_1 = Incident(send_email_upon_creation=False)
        incident_report_2 = Incident(send_email_upon_creation=False)
        loc = IncidentLocation(
            latitude='39.951039',
            longitude='-75.197428',
            original_user_text='3700 Spruce St.',
            incident_report=incident_report_1
        )
        self.assertEqual(loc.incident_report, incident_report_1)
        loc.incident_report = incident_report_2
        self.assertEqual(loc.incident_report, incident_report_2)

    def test_incident_no_location(self):
        now = datetime.datetime.now()
        incident = Incident(
            pedestrian_num=0,
            bicycle_num=1,
            automobile_num=1,
            other_num=0,
            date=now,
            picture_url='http://google.com',
            description='Truck idling on the road!',
            send_email_upon_creation=False
        )
        self.assertEqual(incident.pedestrian_num, 0)
        self.assertEqual(incident.bicycle_num, 1)
        self.assertEqual(incident.automobile_num, 1)
        self.assertEqual(incident.other_num, 0)
        self.assertEqual(incident.picture_url, 'http://google.com')
        self.assertEqual(incident.description, 'Truck idling on the road!')

    def test_incident_report_with_location_no_agency(self):
        loc1 = Location(
            latitude='39.951021',
            longitude='-75.197243',
            original_user_text='3700 Spruce St.'
        )
        loc2 = Location(
            latitude='',
            longitude='-75.197428',
            original_user_text='3800 Spruce St.'
        )
        incident = Incident(
            pedestrian_num=0,
            bicycle_num=1,
            automobile_num=1,
            other_num=0,
            date=now,
            loc=loc1
            picture_url='http://google.com',
            description='Truck idling on the road!',
            send_email_upon_creation=False
        )
        self.assertEqual(incident.location, loc1)
        incident.location = loc2
        self.assertEqual(incident.location, loc2)

    def test_incident_report_with_contact(self):
        incident = Incident(
            pedestrian_num=0,
            bicycle_num=1,
            automobile_num=1,
            other_num=0,
            date=now,
            loc=loc1
            picture_url='http://google.com',
            description='Truck idling on the road!',
            contact_name="Bob",
            contact_phone=1234567890,
            contact_email="one@two.com",
            send_email_upon_creation=False
        )
        self.assertEqual(incident.name, "Bob")
        self.assertEqual(incident.contact_phone, 1234567890)
        self.assertEqual(incident.contact_email, "one@two.com")
