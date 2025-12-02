"""
Helper command to get authentication cookie for Lighthouse CI.

This command logs in as a superuser and outputs the session cookie
that can be used by Lighthouse CI to authenticate requests.
"""

import os
import sys
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.test import Client
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = "Get authentication cookie for Lighthouse CI audits."

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for superuser (default: first superuser found)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for superuser (if not provided, will try to create/use test user)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        password = options.get('password')

        # Try to get or create a test superuser
        if username:
            try:
                user = User.objects.get(username=username, is_superuser=True)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Superuser with username "{username}" not found.')
                )
                sys.exit(1)
        else:
            # Get first superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # Create a test superuser for Lighthouse
                username = 'lighthouse_test'
                password = 'lighthouse_test_password_123'
                user = User.objects.create_superuser(
                    username=username,
                    email='lighthouse@test.com',
                    password=password,
                )
                self.stdout.write(
                    self.style.WARNING(
                        f'Created test superuser: {username} / {password}'
                    )
                )

        # Use provided password or set a known password for test user
        if not password:
            if user.username == 'lighthouse_test':
                password = 'lighthouse_test_password_123'
            else:
                self.stdout.write(
                    self.style.ERROR(
                        'Password required for existing superuser. Use --password or --username lighthouse_test'
                    )
                )
                sys.exit(1)

        # Set password if it's the test user
        if user.username == 'lighthouse_test':
            user.set_password(password)
            user.save()

        # Authenticate and get cookie
        client = Client()
        login_success = client.login(username=user.username, password=password)

        if not login_success:
            self.stdout.write(self.style.ERROR('Failed to login.'))
            sys.exit(1)

        # Get session cookie
        session_cookie = client.cookies.get(settings.SESSION_COOKIE_NAME)
        if not session_cookie:
            self.stdout.write(self.style.ERROR('Failed to get session cookie.'))
            sys.exit(1)

        # Output cookie in format Lighthouse CI can use
        cookie_value = session_cookie.value
        cookie_name = settings.SESSION_COOKIE_NAME

        # Output for Lighthouse CI (cookie format: name=value)
        self.stdout.write(f'{cookie_name}={cookie_value}')

