"""
Management command to run Lighthouse audits on all pages.

Usage:
    python manage.py run_lighthouse_audit
    python manage.py run_lighthouse_audit --url-name editais_index
    python manage.py run_lighthouse_audit --base-url http://localhost:8000
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.urls import get_resolver, reverse, NoReverseMatch
from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Run Lighthouse audits on all pages of the site'

    def add_arguments(self, parser):
        parser.add_argument(
            '--base-url',
            type=str,
            default='http://localhost:8000',
            help='Base URL for the site (default: http://localhost:8000)'
        )
        parser.add_argument(
            '--url-name',
            type=str,
            default=None,
            help='Run audit only on a specific URL name'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Directory to save Lighthouse reports (default: lighthouse_reports/)'
        )
        parser.add_argument(
            '--categories',
            type=str,
            default='performance,accessibility,best-practices,seo',
            help='Comma-separated list of categories to audit'
        )

    def handle(self, *args, **options):
        base_url = options['base_url']
        url_name = options.get('url_name')
        output_dir = options.get('output_dir') or Path(settings.BASE_DIR) / 'lighthouse_reports'
        categories = options['categories'].split(',')

        # Check if lighthouse is installed
        if not self.check_lighthouse_installed():
            self.stdout.write(
                self.style.ERROR('Lighthouse is not installed.')
            )
            self.stdout.write('Install it with: npm install -g lighthouse')
            raise CommandError('Lighthouse not found. Please install it first.')

        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get authentication cookie
        auth_cookie = self.get_auth_cookie(base_url)
        if auth_cookie:
            self.stdout.write(self.style.SUCCESS('Authenticated as superuser\n'))
        else:
            self.stdout.write(self.style.WARNING('Could not authenticate - some pages may fail\n'))

        # Discover URLs
        urls = self.discover_urls(url_name)
        
        if not urls:
            self.stdout.write(self.style.WARNING('No URLs found to audit.'))
            return

        self.stdout.write(
            self.style.SUCCESS(f'Found {len(urls)} URLs to audit.\n')
        )

        # Run audits
        for i, (url_path, url_name) in enumerate(urls, 1):
            full_url = urljoin(base_url, url_path)
            self.stdout.write(
                f'[{i}/{len(urls)}] Auditing: {url_name or url_path}'
            )
            self.stdout.write(f'  URL: {full_url}')
            
            try:
                self.run_lighthouse_audit(
                    full_url,
                    url_name or url_path,
                    output_dir,
                    categories,
                    auth_cookie
                )
                self.stdout.write(self.style.SUCCESS('  [OK] Completed\n'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] {str(e)}\n'))

        self.stdout.write(
            self.style.SUCCESS(f'\nAll audits completed. Reports saved to: {output_dir}')
        )
    
    def get_auth_cookie(self, base_url: str) -> Optional[str]:
        """Login and get session cookie for authenticated requests"""
        try:
            # Get or create superuser
            superuser = User.objects.filter(is_superuser=True).first()
            if not superuser:
                # Create superuser
                superuser = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='admin123'
                )
                self.stdout.write('Created superuser: admin/admin123')
            else:
                # Reset password to known value for existing superuser
                superuser.set_password('admin123')
                superuser.save()
            
            # Login using test client (Django's login method)
            client = Client()
            login_success = client.login(username=superuser.username, password='admin123')
            
            if login_success:
                # Extract session cookie
                cookies = client.cookies
                session_cookie = cookies.get(settings.SESSION_COOKIE_NAME)
                if session_cookie:
                    return f"{settings.SESSION_COOKIE_NAME}={session_cookie.value}"
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Auth failed: {e}'))
        return None

    def check_lighthouse_installed(self) -> bool:
        """Check if lighthouse CLI is installed"""
        # Try lighthouse directly first
        try:
            result = subprocess.run(
                ['lighthouse', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True  # Use shell on Windows
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try npx lighthouse as fallback
        try:
            result = subprocess.run(
                ['npx', '--yes', 'lighthouse', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                shell=True
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def discover_urls(self, url_name: Optional[str] = None) -> List[tuple]:
        """
        Discover all URLs from Django URL patterns.
        Returns list of tuples: (url_path, url_name)
        """
        urls = []
        resolver = get_resolver()

        def extract_urls(patterns, prefix=''):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
                elif hasattr(pattern, 'name') and pattern.name:
                    try:
                        # Skip admin URLs
                        if 'admin' in pattern.name or 'admin' in prefix:
                            continue
                        
                        # Filter by url_name if specified
                        if url_name and pattern.name != url_name:
                            continue
                        
                        # Try to reverse URL
                        try:
                            url_path = reverse(pattern.name)
                            urls.append((url_path, pattern.name))
                        except NoReverseMatch:
                            # URL requires arguments, skip
                            continue
                    except Exception:
                        continue

        extract_urls(resolver.url_patterns)
        return urls

    def run_lighthouse_audit(
        self,
        url: str,
        url_name: str,
        output_dir: Path,
        categories: List[str],
        auth_cookie: Optional[str] = None
    ):
        """Run lighthouse audit on a URL and save results"""
        # Create safe filename
        safe_name = url_name.replace('/', '_').replace('-', '_')
        
        # Build lighthouse command - try npx if lighthouse not found
        try:
            # Try lighthouse directly first
            subprocess.run(['lighthouse', '--version'], capture_output=True, shell=True, timeout=2)
            lighthouse_cmd = 'lighthouse'
        except:
            # Fallback to npx
            lighthouse_cmd = 'npx'
            if lighthouse_cmd == 'npx':
                cmd = ['npx', '--yes', 'lighthouse', url]
            else:
                cmd = ['lighthouse', url]
        else:
            cmd = ['lighthouse', url]
        
        # Build command with authentication
        import os
        env = os.environ.copy()
        
        cmd.extend([
            '--output=json,html',
            f'--output-path={output_dir / safe_name}',
            '--quiet',
            '--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage',
            '--only-categories=' + ','.join(categories),
            '--no-enable-error-reporting',
        ])
        
        # Add authentication cookie if available
        if auth_cookie:
            # Use extra-headers for cookies
            import json as json_lib
            headers = {"Cookie": auth_cookie}
            cmd.append(f'--extra-headers={json_lib.dumps(headers)}')
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            shell=True,  # Use shell on Windows
            env=env
        )
        
        if result.returncode != 0:
            raise Exception(f"Lighthouse failed: {result.stderr[:200]}")
        
        # Parse and display scores
        json_path = output_dir / f'{safe_name}.json'
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            categories_data = data.get('categories', {})
            scores = {}
            for cat in ['performance', 'accessibility', 'best-practices', 'seo']:
                if cat in categories_data:
                    score = categories_data[cat].get('score', 0) * 100
                    scores[cat] = score
                    color = self.style.SUCCESS if score >= 90 else self.style.WARNING if score >= 70 else self.style.ERROR
                    self.stdout.write(f'    {cat.capitalize()}: {color(f"{score:.1f}")}')

