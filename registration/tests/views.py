import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from registration import forms
from registration.models import RegistrationProfile


class RegistrationViewTests(TestCase):
    """
    Test the registration views.

    """
    urls = 'registration.tests.urls'

    def setUp(self):
        """
        These tests use the default backend, since we know it's
        available; that needs to have ``ACCOUNT_ACTIVATION_DAYS`` set.

        """
        self.old_activation = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', None)
        if self.old_activation is None:
            settings.ACCOUNT_ACTIVATION_DAYS = 7

    def tearDown(self):
        """
        Yank ``ACCOUNT_ACTIVATION_DAYS`` back out if it wasn't
        originally set.

        """
        if self.old_activation is None:
            settings.ACCOUNT_ACTIVATION_DAYS = self.old_activation

                                   
    def test_registration_view_initial(self):
        r = self.client.get(reverse('registration_register'), {}, 
                                )
        self.assertEqual(response.status_code, 200)


    def test_registration_view_success(self):
        """
        A ``POST`` to the ``register`` view with valid data properly
        creates a new user and issues a redirect.

        """
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'alice',
                                          'email': 'alice@example.com',
                                          'password1': 'swordfish',
                                          'password2': 'swordfish'},
                                    )
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotContains(response,'error')
        self.assertContains(response,'success')

        
    def test_registration_view_failure_ajax(self):
        """
        A ``POST`` to the ``register`` view with valid data properly
        creates a new user and issues a redirect.

        """
        response = self.client.post(reverse('registration_register'),
                                    data={'username': 'alice',
                                          'email': 'alice@example.com',
                                          'password1': 'swordfish',
                                          'password2': 'sword'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,'error')


    def test_valid_activation(self):
        """
        Test that the ``activate`` view properly handles a valid
        activation (in this case, based on the default backend's
        activation window).

        """
        
        # First, register an account.
        self.client.post(reverse('registration_register'),
                         data={'username': 'alice',
                               'email': 'alice@example.com',
                               'password1': 'swordfish',
                               'password2': 'swordfish'})
        profile = RegistrationProfile.objects.get(user__username='alice')
        response = self.client.get(reverse('registration_activate',
                                           kwargs={'activation_key': profile.activation_key}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,'success')
        self.failUnless(User.objects.get(username='alice').is_active)
        
        
    def test_invalid_activation(self):
        """
        Test that the ``activate`` view properly handles an invalid
        activation (in this case, based on the default backend's
        activation window).

        """
        # Register an account and reset its date_joined to be outside
        # the activation window.
        self.client.post(reverse('registration_register'),
                         data={'username': 'bob',
                               'email': 'bob@example.com',
                               'password1': 'secret',
                               'password2': 'secret'})
        expired_user = User.objects.get(username='bob')
        expired_user.date_joined = expired_user.date_joined - datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        expired_user.save()

        expired_profile = RegistrationProfile.objects.get(user=expired_user)
        response = self.client.get(reverse('registration_activate',
                                           kwargs={'activation_key': expired_profile.activation_key}))
        self.assertEqual(response.status_code, 200)
        self.failIf(User.objects.get(username='bob').is_active)


