import json
import logging
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


# Configure console logging for tests (ensures logs appear when running `manage.py test`).
logger = logging.getLogger('reports.tests')
if not logger.handlers:
    handler = logging.StreamHandler()

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            message = super().format(record)
            if 'PASSED' in message:
                message = f'\033[92m{message}\033[0m'  # Green for PASSED
            elif 'FAILED' in message:
                message = f'\033[91m{message}\033[0m'  # Red for FAILED
            return message

    handler.setFormatter(ColoredFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class LoggedTestCase(TestCase):
    def run(self, result=None):
        super().run(result)
        name = self.id().split('.')[-1]
        doc = (self._testMethodDoc or '').strip() or 'No description'
        failure_details = None
        if self in [f[0] for f in result.failures]:
            failure_details = [f[1] for f in result.failures if f[0] == self][0]
        elif self in [e[0] for e in result.errors]:
            failure_details = [e[1] for e in result.errors if e[0] == self][0]
        
        if failure_details:
            status = 'FAILED'
            logger.info('> test name - "%s"', name)
            logger.info('> test case - "%s"', doc)
            logger.info('> status - %s', status)
            logger.info('> error details - %s', failure_details.strip())
        else:
            status = 'PASSED'
            logger.info('> test name - "%s"', name)
            logger.info('> test case - "%s"', doc)
            logger.info('> status - %s', status)

from .models import (
    DisasterReport, DisasterUpdate, Feedback, MissingPerson,
    InjuredPerson, Donation, UpdateUpvote,
)


class SmokeTests(LoggedTestCase):
    def test_home_page_loads(self):
        """Basic smoke test to ensure the home page renders without errors."""
        response = self.client.get(reverse('home'))
        logger.info('home page status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertIn('disasters', response.context)

    def test_missing_view_loads(self):
        """Ensure missing-person listing view renders even with no data."""
        response = self.client.get(reverse('view_missing'))
        logger.info('view_missing status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_missing.html')

    def test_can_create_disaster_report_model(self):
        """Sanity-check that models can be created and string conversion works."""
        report = DisasterReport.objects.create(
            disaster_type='Fire',
            location='Testville',
            description='Test report',
        )
        self.assertEqual(str(report), 'Fire at Testville')

    def test_view_disasters_filtering(self):
        """Ensure the disasters listing can be filtered by type."""
        DisasterReport.objects.create(disaster_type='Flood', location='River', description='Flooding')
        DisasterReport.objects.create(disaster_type='Fire', location='Forest', description='Wildfire')

        response = self.client.get(reverse('view_disasters'), {'type': 'Flood'})
        logger.info('view_disasters filter response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'River')
        self.assertNotContains(response, 'Forest')


class AuthTests(LoggedTestCase):
    def test_register_and_login_flow(self):
        response = self.client.post(
            reverse('auth_register'),
            {
                'username': 'tester',
                'email': 'tester@example.com',
                'first_name': 'Tester',
                'password1': 'password123',
                'password2': 'password123',
            },
            follow=True,
        )
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(User.objects.filter(username='tester').exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_clears_session(self):
        user = User.objects.create_user('logoutme', 'a@b.com', 'pass123')
        self.client.login(username='logoutme', password='pass123')
        response = self.client.get(reverse('auth_logout'), follow=True)
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class DonationTests(LoggedTestCase):
    def test_donate_missing_fields_shows_error(self):
        response = self.client.post(
            reverse('donate'),
            {
                'name': '',
                'email': '',
                'amount': '',
                'purpose': '',
                'payment_mode': '',
            },
        )
        logger.info('donate missing fields status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please fill in all required fields.')

    def test_donate_invalid_email_shows_error(self):
        response = self.client.post(
            reverse('donate'),
            {
                'name': 'Donor',
                'email': 'invalid-email',
                'amount': '10.00',
                'purpose': 'Testing',
                'payment_mode': 'Cash',
            },
        )
        logger.info('donate invalid email status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid email address.')

    def test_donate_view_get(self):
        response = self.client.get(reverse('donate'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'donate.html')

    def test_donate_post_success(self):
        response = self.client.post(
            reverse('donate'),
            {
                'name': 'Donor',
                'email': 'donor@example.com',
                'amount': '10.50',
                'purpose': 'Testing',
                'payment_mode': 'Cash',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('donation_success'))
        self.assertTrue(Donation.objects.filter(name='Donor').exists())

    def test_donate_post_invalid_amount(self):
        response = self.client.post(
            reverse('donate'),
            {
                'name': 'Donor',
                'email': 'donor@example.com',
                'amount': '-5',
                'purpose': 'Testing',
                'payment_mode': 'Cash',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid donation amount.')


class LivePopulationApiTests(LoggedTestCase):
    @patch('reports.views.reverse_geocode')
    @patch('reports.views.get_crowd_for_location')
    def test_get_live_population_success(self, mock_crowd, mock_reverse):
        mock_crowd.return_value = (123, 'Moderate')
        mock_reverse.return_value = ('State', 'City')

        response = self.client.post(
            reverse('get_live_population'),
            data=json.dumps({'latitude': 1.2, 'longitude': 3.4, 'radius': 5}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['population'], 123)
        self.assertEqual(data['level'], 'Moderate')
        self.assertEqual(data['city'], 'City')

    def test_get_live_population_requires_post(self):
        response = self.client.get(reverse('get_live_population'))
        self.assertEqual(response.status_code, 405)


class ReportDisasterTests(LoggedTestCase):
    @patch('reports.views.get_crowd_for_location')
    @patch('reports.views.geocode_address')
    def test_report_disaster_success(self, mock_geocode, mock_crowd):
        mock_geocode.return_value = (12.34, 56.78)
        mock_crowd.return_value = (100, 'Moderate')

        response = self.client.post(
            reverse('report_disaster'),
            {
                'disaster_type': 'Fire',
                'location': 'Test City',
                'description': 'Test',
                'latitude': '12.34',
                'longitude': '56.78',
            },
            follow=True,
        )
        logger.info('report_disaster status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(DisasterReport.objects.filter(location='Test City').exists())


class DisasterDetailTests(LoggedTestCase):
    def setUp(self):
        self.disaster = DisasterReport.objects.create(
            disaster_type='Fire',
            location='Detailville',
            description='Detail report',
        )
        self.update = DisasterUpdate.objects.create(
            disaster=self.disaster, author_name='Tester', content='An update',
        )

    def test_upvote_increments_and_debounces(self):
        url = reverse('disaster_detail', kwargs={'pk': self.disaster.pk})

        first = self.client.post(
            url,
            {'action': 'upvote', 'update_id': self.update.pk},
            REMOTE_ADDR='1.2.3.4',
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()['upvotes'], 1)
        self.assertFalse(first.json()['already_voted'])

        second = self.client.post(
            url,
            {'action': 'upvote', 'update_id': self.update.pk},
            REMOTE_ADDR='1.2.3.4',
        )
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()['already_voted'])

        self.assertEqual(UpdateUpvote.objects.filter(update=self.update).count(), 1)

    def test_post_update_adds_comment(self):
        url = reverse('disaster_detail', kwargs={'pk': self.disaster.pk})
        response = self.client.post(
            url,
            {'action': 'post_update', 'author_name': 'Anon', 'content': 'New update'},
            follow=True,
        )
        logger.info('post_update response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(DisasterUpdate.objects.filter(content='New update').exists())


class FeedbackTests(LoggedTestCase):
    def test_submit_feedback_requires_message(self):
        response = self.client.post(reverse('feedback'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please describe the issue.')

    def test_submit_feedback_saves(self):
        response = self.client.post(
            reverse('feedback'),
            {'message': 'Great app!'},
            follow=True,
        )
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(Feedback.objects.filter(message='Great app!').exists())


class AdminDashboardSecurityTests(LoggedTestCase):
    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('auth_login'), response['Location'])

    def test_admin_dashboard_renders_for_logged_in_user(self):
        user = User.objects.create_user('admin', 'admin@example.com', 'pass123')
        self.client.login(username='admin', password='pass123')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_dashboard.html')


class MissingReportTests(LoggedTestCase):
    def setUp(self):
        self.user = User.objects.create_user('reporter', 'reporter@example.com', 'pass123')
        self.client.login(username='reporter', password='pass123')

    def test_report_missing_creates_record(self):
        response = self.client.post(
            reverse('report_missing'),
            {
                'name': 'Alice',
                'age': '30',
                'gender': 'Female',
                'location': 'Nowhere',
                'body_marks': 'None',
            },
            follow=True,
        )
        logger.info('report_missing response status: %s', response.status_code)
        self.assertRedirects(response, reverse('view_missing'))
        self.assertTrue(MissingPerson.objects.filter(name='Alice').exists())

    def test_report_missing_invalid_age_shows_error(self):
        response = self.client.post(
            reverse('report_missing'),
            {
                'name': 'Bob',
                'age': 'abc',
                'gender': 'Male',
                'location': 'Somewhere',
                'body_marks': 'Scar',
            },
        )
        logger.info('invalid age response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid age.')

    def test_update_missing_status_changes_record(self):
        person = MissingPerson.objects.create(
            name='Tom', age=40, gender='Male',
            last_seen_location='Here', body_marks='None',
        )
        response = self.client.post(
            reverse('update_missing_status', kwargs={'pk': person.pk}),
            {'status': 'Found', 'status_note': 'Located'},
            follow=True,
        )
        logger.info('update_missing_status response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        person.refresh_from_db()
        self.assertEqual(person.status, 'Found')


class ReportInjuredTests(LoggedTestCase):
    def setUp(self):
        self.user = User.objects.create_user('injured_reporter', 'injured@example.com', 'pass123')
        self.client.login(username='injured_reporter', password='pass123')

    def test_report_injured_creates_record(self):
        response = self.client.post(
            reverse('report_injured'),
            {
                'name': 'Charlie',
                'age': '25',
                'gender': 'Male',
                'injury_type': 'Broken Leg',
                'severity': 'Moderate',
                'location': 'Hospital',
                'description': 'Fell from ladder',
            },
            follow=True,
        )
        logger.info('report_injured response status: %s', response.status_code)
        self.assertRedirects(response, reverse('view_injured'))
        self.assertTrue(InjuredPerson.objects.filter(name='Charlie').exists())

    def test_report_injured_invalid_age_shows_error(self):
        response = self.client.post(
            reverse('report_injured'),
            {
                'name': 'Dana',
                'age': 'invalid',
                'gender': 'Female',
                'injury_type': 'Sprain',
                'severity': 'Minor',
                'location': 'Clinic',
                'description': 'Twisted ankle',
            },
        )
        logger.info('report_injured invalid age status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a valid age.')

    def test_update_injured_status_changes_record(self):
        from .models import InjuredPerson
        person = InjuredPerson.objects.create(
            name='Eve', age=35, gender='Female',
            injury_type='Burn', severity='Critical',
            location='Burn Unit', description='Severe burn',
        )
        response = self.client.post(
            reverse('update_injured_status', kwargs={'pk': person.pk}),
            {'status': 'Recovering', 'status_note': 'Improving'},
            follow=True,
        )
        logger.info('update_injured_status response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        person.refresh_from_db()
        self.assertEqual(person.status, 'Recovering')


class HeatmapTests(LoggedTestCase):
    def test_heatmap_data_returns_json(self):
        DisasterReport.objects.create(
            disaster_type='Fire', location='Map City',
            latitude=10.0, longitude=20.0, description='Fire on map',
        )
        response = self.client.get(reverse('heatmap_data'))
        logger.info('heatmap_data response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('points', data)
        self.assertIn('stats', data)
        self.assertGreater(len(data['points']), 0)

    def test_heatmap_page_loads(self):
        response = self.client.get(reverse('disaster_heatmap'))
        logger.info('disaster_heatmap response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'disaster_heatmap.html')


class FeedbackTests(LoggedTestCase):
    def test_submit_feedback_requires_message(self):
        response = self.client.post(reverse('feedback'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please describe the issue.')

    def test_submit_feedback_saves(self):
        response = self.client.post(
            reverse('feedback'),
            {'message': 'Great app!'},
            follow=True,
        )
        self.assertRedirects(response, reverse('home'))
        self.assertTrue(Feedback.objects.filter(message='Great app!').exists())

    def test_submit_feedback_with_logged_in_user(self):
        user = User.objects.create_user('feedback_user', 'fb@example.com', 'pass123')
        self.client.login(username='feedback_user', password='pass123')
        response = self.client.post(
            reverse('feedback'),
            {'message': 'Logged in feedback'},
            follow=True,
        )
        logger.info('feedback with user status: %s', response.status_code)
        self.assertRedirects(response, reverse('home'))
        fb = Feedback.objects.get(message='Logged in feedback')
        self.assertEqual(fb.reporter_name, user.get_full_name() or user.username)
        self.assertEqual(fb.reporter_email, user.email)


class AdminDashboardTests(LoggedTestCase):
    def setUp(self):
        self.user = User.objects.create_user('admin', 'admin@example.com', 'pass123')
        self.client.login(username='admin', password='pass123')

    def test_admin_dashboard_shows_counts(self):
        DisasterReport.objects.create(disaster_type='Fire', location='Admin City', description='Admin fire')
        Donation.objects.create(name='Admin Donor', email='admin@donor.com', amount=50.00, purpose='Admin', payment_mode='Cash')
        response = self.client.get(reverse('admin_dashboard'))
        logger.info('admin_dashboard response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1')  # At least one disaster
        self.assertContains(response, '50')  # Donation amount

    def test_resolve_feedback_marks_resolved(self):
        fb = Feedback.objects.create(message='To resolve', reporter_name='Anon')
        response = self.client.post(
            reverse('resolve_feedback', kwargs={'pk': fb.pk}),
            follow=True,
        )
        logger.info('resolve_feedback response status: %s', response.status_code)
        self.assertEqual(response.status_code, 200)
        fb.refresh_from_db()
        self.assertTrue(fb.resolved)
