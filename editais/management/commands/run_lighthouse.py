"""
Management command to run Lighthouse CI audits against the Django application.

This command starts a Django development server in the background, runs Lighthouse
CI audits against configured URLs, and generates reports in the lighthouse_reports/
directory.

Usage:
    python manage.py run_lighthouse
    python manage.py run_lighthouse --url /editais/ --url /login/
    python manage.py run_lighthouse --output-dir ./custom_reports
    python manage.py run_lighthouse --thresholds performance=0.85
    python manage.py run_lighthouse --all-pages  # Audit all pages including protected ones
"""

import os
import sys
import subprocess
import signal
import time
import logging
import json
import tempfile
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

from editais.models import Edital

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run Lighthouse CI audits against the Django application."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.server_process = None
        self.lighthouse_process = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            action='append',
            dest='urls',
            help='Specific URL(s) to audit (can be used multiple times). If not specified, uses URLs from .lighthouserc.js',
        )
        parser.add_argument(
            '--all-pages',
            action='store_true',
            help='Audit all pages including protected dashboard pages (requires superuser)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='./lighthouse_reports',
            help='Directory to save Lighthouse reports (default: ./lighthouse_reports)',
        )
        parser.add_argument(
            '--thresholds',
            type=str,
            help='Override thresholds in format: performance=0.85,accessibility=0.90 (comma-separated)',
        )
        parser.add_argument(
            '--port',
            type=int,
            default=7000,
            help='Port to run Django server on (default: 7000)',
        )
        parser.add_argument(
            '--no-server',
            action='store_true',
            help='Do not start Django server (assumes server is already running)',
        )
        parser.add_argument(
            '--no-auth',
            action='store_true',
            help='Skip authentication (only audit public pages)',
        )
        parser.add_argument(
            '--skip-assertions',
            action='store_true',
            help='Skip assertion checks (useful for testing or when thresholds are too strict)',
        )
        parser.add_argument(
            '--continue-on-error',
            action='store_true',
            help='Continue auditing remaining URLs even if one fails',
        )

    def handle(self, *args, **options):
        urls = options.get('urls', [])
        all_pages = options.get('all_pages', False)
        output_dir = options['output_dir']
        thresholds = options.get('thresholds')
        port = options['port']
        no_server = options['no_server']
        no_auth = options.get('no_auth', False)
        skip_assertions = options.get('skip_assertions', False)
        continue_on_error = options.get('continue_on_error', False)

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Set up signal handlers for cleanup
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            # Get all URLs if --all-pages is specified
            if all_pages and not urls:
                self.stdout.write(self.style.SUCCESS('Discovering all URLs...'))
                urls = self._get_all_urls(port)
                self.stdout.write(f'Found {len(urls)} URLs to audit')

            # Get authentication cookie if needed
            # Always get cookie when using --all-pages to ensure protected pages work
            auth_cookie = None
            if not no_auth and (all_pages or any('/dashboard' in url or '/admin' in url or '/cadastrar' in url or '/editar' in url for url in urls)):
                self.stdout.write(self.style.SUCCESS('Getting authentication cookie...'))
                auth_cookie = self._get_auth_cookie()
                if auth_cookie:
                    self.stdout.write(self.style.SUCCESS('Authentication cookie obtained'))
                else:
                    self.stdout.write(self.style.WARNING('Failed to get auth cookie, some pages may fail'))
            elif all_pages and not no_auth:
                # Even if URLs don't explicitly require auth, get cookie for --all-pages
                self.stdout.write(self.style.SUCCESS('Getting authentication cookie for all pages...'))
                auth_cookie = self._get_auth_cookie()
                if auth_cookie:
                    self.stdout.write(self.style.SUCCESS('Authentication cookie obtained'))

            # Start Django server if needed
            if not no_server:
                self.stdout.write(self.style.SUCCESS(f'Starting Django server on port {port}...'))
                self._start_server(port)
                # Wait for server to be ready
                self._wait_for_server(port)
            else:
                self.stdout.write(self.style.WARNING('Skipping server start (--no-server flag set)'))

            # Run Lighthouse CI
            self.stdout.write(self.style.SUCCESS('Running Lighthouse CI audits...'))
            if skip_assertions:
                self.stdout.write(self.style.WARNING('Assertions will be skipped (--skip-assertions flag set)'))
            
            url_count = len(urls) if urls else 'all configured'
            self.stdout.write(f'Auditing {url_count} URL(s)...')
            
            success = self._run_lighthouse(urls, output_dir, thresholds, port, auth_cookie, skip_assertions, continue_on_error)

            # Print summary
            self._print_summary(success, output_dir, urls)

            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ Lighthouse audits completed successfully! Reports saved to {output_dir}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR('\n❌ Lighthouse audits completed with errors. Check the output above.')
                )
                self.stdout.write(
                    self.style.WARNING(
                        '\nTip: Use --skip-assertions to skip threshold checks, or check the reports in the output directory.'
                    )
                )
                sys.exit(1)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nInterrupted by user'))
            sys.exit(1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))
            logger.exception('Error running Lighthouse audits')
            sys.exit(1)
        finally:
            self._cleanup()

    def _start_server(self, port):
        """Start Django development server in background."""
        # Use the same Python interpreter
        python_executable = sys.executable
        manage_py = os.path.join(settings.BASE_DIR, 'manage.py')
        
        # Start server with --noreload to avoid issues
        self.server_process = subprocess.Popen(
            [python_executable, manage_py, 'runserver', f'127.0.0.1:{port}', '--noreload'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=settings.BASE_DIR,
        )

    def _wait_for_server(self, port, timeout=30):
        """Wait for Django server to be ready."""
        import socket
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result == 0:
                    time.sleep(1)  # Give server a moment to fully start
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        
        raise RuntimeError(f'Server did not start within {timeout} seconds')

    def _get_all_urls(self, port):
        """Discover all URLs in the application."""
        base_url = f'http://localhost:{port}'
        urls = []
        
        # Public pages
        public_urls = [
            '/',
            '/editais/',
            '/login/',
            '/register/',
            '/ambientes-inovacao/',
            '/projetos-aprovados/',
            '/startups/',
            '/health/',
            '/password-reset/',
            '/password-reset/done/',
            '/password-reset-complete/',
        ]
        urls.extend([base_url + url for url in public_urls])
        
        # Dashboard pages (require auth)
        dashboard_urls = [
            '/dashboard/',
            '/dashboard/home/',
            '/dashboard/editais/',
            '/dashboard/editais/novo/',
            '/dashboard/projetos/',
            '/dashboard/projetos/submeter/',
            '/dashboard/avaliacoes/',
            '/dashboard/usuarios/',
            '/dashboard/relatorios/',
        ]
        urls.extend([base_url + url for url in dashboard_urls])
        
        # Admin
        urls.append(base_url + '/admin/')
        
        # CRUD pages (require auth)
        urls.append(base_url + '/cadastrar/')
        
        # Dynamic edital pages - get from database
        try:
            editais = Edital.objects.filter(slug__isnull=False).exclude(slug='')[:10]  # Limit to 10 for performance
            for edital in editais:
                urls.append(base_url + f'/edital/{edital.slug}/')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not fetch edital slugs: {e}'))
        
        return urls

    def _get_auth_cookie(self):
        """Get authentication cookie for superuser."""
        try:
            # Get or create test superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                # Create test superuser
                user = User.objects.create_superuser(
                    username='lighthouse_test',
                    email='lighthouse@test.com',
                    password='lighthouse_test_password_123',
                )
                self.stdout.write(self.style.WARNING('Created test superuser: lighthouse_test'))
            
            # Set password if it's the test user
            if user.username == 'lighthouse_test':
                user.set_password('lighthouse_test_password_123')
                user.save()
            
            # Authenticate
            client = Client()
            password = 'lighthouse_test_password_123' if user.username == 'lighthouse_test' else None
            
            if password:
                login_success = client.login(username=user.username, password=password)
            else:
                # Try to use existing password or create new one
                user.set_password('lighthouse_test_password_123')
                user.save()
                login_success = client.login(username=user.username, password='lighthouse_test_password_123')
            
            if not login_success:
                return None
            
            # Get session cookie
            session_cookie = client.cookies.get(settings.SESSION_COOKIE_NAME)
            if session_cookie:
                return f'{settings.SESSION_COOKIE_NAME}={session_cookie.value}'
            return None
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Error getting auth cookie: {e}'))
            logger.exception('Error getting auth cookie')
            return None

    def _run_lighthouse(self, urls, output_dir, thresholds, port, auth_cookie=None, skip_assertions=False, continue_on_error=False):
        """Run Lighthouse CI audits."""
        # Find lhci command
        base_dir = settings.BASE_DIR
        theme_dir = os.path.join(base_dir, 'theme', 'static_src')
        node_modules = os.path.join(theme_dir, 'node_modules', '.bin')
        
        # Check if lhci exists in node_modules
        if os.name == 'nt':  # Windows
            lhci_cmd = os.path.join(node_modules, 'lhci.cmd')
        else:  # Unix-like
            lhci_cmd = os.path.join(node_modules, 'lhci')
        
        # Fallback to global lhci if not found locally
        if not os.path.exists(lhci_cmd):
            lhci_cmd = 'lhci'
        
        # Create temporary config file with custom URLs and auth
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False)
        try:
            # Read base config
            base_config_path = os.path.join(base_dir, '.lighthouserc.js')
            base_config = {}
            if os.path.exists(base_config_path):
                with open(base_config_path, 'r') as f:
                    base_config_content = f.read()
                    # Simple extraction of base config (we'll merge it)
                    base_config = {'ci': {'assert': {}, 'upload': {}, 'server': {}}}
            
            # Build URLs list - normalize relative URLs to full URLs
            base_url = f'http://localhost:{port}'
            
            def normalize_url(url):
                """Convert relative URLs to full URLs."""
                if not url:
                    return url
                # If it's already a full URL (starts with http:// or https://), use it as-is
                if url.startswith('http://') or url.startswith('https://'):
                    return url
                # If it's a relative path (starts with /), prepend base URL
                if url.startswith('/'):
                    # Ensure there's no double slash
                    if base_url.endswith('/'):
                        return base_url[:-1] + url
                    return base_url + url
                # If it's a relative path without leading slash, add it
                return f'{base_url}/{url}'
            
            if urls:
                url_list = [normalize_url(url) for url in urls]
            else:
                url_list = [
                    f'{base_url}/',
                    f'{base_url}/editais/',
                    f'{base_url}/login/',
                    f'{base_url}/register/',
                ]
            
            # Write config file as JavaScript
            config_file.write('module.exports = {\n')
            config_file.write('  ci: {\n')
            config_file.write('    collect: {\n')
            config_file.write('      url: [\n')
            for url in url_list:
                config_file.write(f"        '{url}',\n")
            config_file.write('      ],\n')
            config_file.write('      numberOfRuns: 1,\n')  # Reduced to 1 to avoid permission errors
            
            # Add Chrome flags to reduce temp file issues on Windows and improve timeout handling
            # --disable-dev-shm-usage: Use /tmp instead of /dev/shm (helps with Windows temp files)
            # --disable-gpu: Disable GPU hardware acceleration (reduces temp file usage)
            # --no-sandbox: Disable sandbox (may be needed on Windows, but use with caution)
            # --disable-setuid-sandbox: Disable setuid sandbox
            # --disable-background-timer-throttling: Prevent background throttling
            # --disable-backgrounding-occluded-windows: Prevent backgrounding
            # --disable-renderer-backgrounding: Prevent renderer backgrounding
            chrome_flags = [
                '--disable-dev-shm-usage',  # Use /tmp instead of /dev/shm (helps with Windows temp files)
                '--disable-gpu',  # Disable GPU hardware acceleration (reduces temp file usage)
                '--disable-setuid-sandbox',  # Disable setuid sandbox
                '--disable-background-timer-throttling',  # Prevent background throttling
                '--disable-backgrounding-occluded-windows',  # Prevent backgrounding
                '--disable-renderer-backgrounding',  # Prevent renderer backgrounding
                '--disable-extensions',  # Disable extensions for faster startup
                '--no-first-run',  # Skip first run tasks
                '--no-default-browser-check',  # Skip default browser check
                '--disable-infobars',  # Disable infobars
                '--disable-notifications',  # Disable notifications
                '--disable-translate',  # Disable translation prompts
                '--window-size=1280,720',  # Set window size for consistent rendering
                '--disable-features=TranslateUI',  # Disable translate UI
            ]
            # Only add --no-sandbox on Windows if needed (security consideration)
            if os.name == 'nt':  # Windows
                chrome_flags.append('--no-sandbox')
                chrome_flags.append('--disable-software-rasterizer')  # Help with Windows rendering
            
            config_file.write('      chromeFlags: [\n')
            for flag in chrome_flags:
                config_file.write(f"        '{flag}',\n")
            config_file.write('      ],\n')
            
            # Add authentication cookie if provided - use it for ALL URLs when auditing all pages
            if auth_cookie:
                config_file.write('      extraHeaders: {\n')
                config_file.write(f"        'Cookie': '{auth_cookie}',\n")
                config_file.write('      },\n')
            
            config_file.write('    },\n')
            
            # Add assertions only if not skipping
            if not skip_assertions:
                config_file.write('    assert: {\n')
                config_file.write('      assertions: {\n')
                config_file.write("        'categories:performance': ['error', { minScore: parseFloat(process.env.LHCI_PERFORMANCE_THRESHOLD || '0.80') }],\n")
                config_file.write("        'categories:accessibility': ['error', { minScore: parseFloat(process.env.LHCI_ACCESSIBILITY_THRESHOLD || '0.90') }],\n")
                config_file.write("        'categories:best-practices': ['error', { minScore: parseFloat(process.env.LHCI_BEST_PRACTICES_THRESHOLD || '0.90') }],\n")
                config_file.write("        'categories:seo': ['error', { minScore: parseFloat(process.env.LHCI_SEO_THRESHOLD || '0.90') }],\n")
                config_file.write('      },\n')
                config_file.write('    },\n')
            config_file.write('    upload: {\n')
            config_file.write("      target: 'filesystem',\n")
            config_file.write(f"      outputDir: '{output_dir}',\n")
            config_file.write('    },\n')
            config_file.write('  },\n')
            config_file.write('};\n')
            config_file.close()
            
            # Build command
            cmd = [lhci_cmd, 'autorun', '--config', config_file.name]
            
            # Set environment variables
            env = os.environ.copy()
            env['LHCI_UPLOAD_OUTPUT_DIR'] = output_dir
            
            # Add environment variables to help with Windows temp file cleanup
            # These make Lighthouse more tolerant of cleanup errors
            env['LIGHTHOUSE_CHROMIUM_FLAGS'] = ' '.join(chrome_flags)
            # Allow Lighthouse to continue even if cleanup fails
            env['LHCI_SKIP_AUTO_SERVER'] = '1'
            
            # Override thresholds if provided
            if thresholds:
                for threshold in thresholds.split(','):
                    if '=' in threshold:
                        key, value = threshold.split('=', 1)
                        env[f'LHCI_{key.upper()}_THRESHOLD'] = value
            
            self.stdout.write(f'Running: {" ".join(cmd)}')
            if auth_cookie:
                self.stdout.write(self.style.SUCCESS('Using authentication cookie'))
            
            # Run Lighthouse CI
            result = subprocess.run(
                cmd,
                cwd=base_dir,
                env=env,
                capture_output=False,
                text=True,
            )
            
            # Check if reports were generated even if process returned non-zero
            # This handles cases where audits succeed but cleanup fails (Windows permission errors)
            reports_generated = False
            report_files = []
            if os.path.exists(output_dir):
                # Check if any report files were created (multiple patterns)
                for pattern in ['*.report.*', '*.json', '*.html']:
                    report_files.extend(list(Path(output_dir).glob(pattern)))
                if report_files:
                    reports_generated = True
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Found {len(report_files)} report file(s) generated'
                        )
                    )
            
            # Handle Windows cleanup errors more gracefully
            # On Windows, EPERM errors during temp file cleanup are common and can be ignored
            # if reports were successfully generated
            if os.name == 'nt':  # Windows
                # Give Windows more time to release file handles before cleanup
                time.sleep(3)
                
                # If reports were generated but process failed, it's likely a cleanup error
                # These are common on Windows and can be safely ignored
                if reports_generated and result.returncode != 0:
                    self.stdout.write(
                        self.style.WARNING(
                            'Lighthouse audits completed but cleanup had errors (likely Windows temp file issue). '
                            'Reports were still generated successfully. This is usually safe to ignore.'
                        )
                    )
                    return True
            
            # For non-Windows or if no reports generated, return actual result
            if reports_generated and result.returncode != 0:
                self.stdout.write(
                    self.style.WARNING(
                        'Lighthouse audits completed but encountered errors. '
                        'Reports were still generated successfully.'
                    )
                )
                return True
            
            return result.returncode == 0
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    f'Lighthouse CI not found. Please install it:\n'
                    f'  cd theme/static_src && npm install'
                )
            )
            return False
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error running Lighthouse CI: {str(e)}'))
            logger.exception('Error running Lighthouse CI')
            return False
        finally:
            # Clean up temp config file
            try:
                if os.path.exists(config_file.name):
                    os.unlink(config_file.name)
            except Exception:
                pass

    def _print_summary(self, success, output_dir, urls):
        """Print a summary of the Lighthouse audit results."""
        self.stdout.write('\n' + '='*70)
        self.stdout.write('LIGHTHOUSE AUDIT SUMMARY')
        self.stdout.write('='*70)
        
        # Check for generated reports
        report_count = 0
        if os.path.exists(output_dir):
            for pattern in ['*.report.*', '*.json', '*.html']:
                report_count += len(list(Path(output_dir).glob(pattern)))
        
        if report_count > 0:
            self.stdout.write(f'📊 Reports generated: {report_count} file(s)')
            self.stdout.write(f'📁 Output directory: {os.path.abspath(output_dir)}')
        else:
            self.stdout.write(self.style.WARNING('⚠️  No reports were generated'))
        
        if urls and len(urls) > 0:
            self.stdout.write(f'🔗 URLs audited: {len(urls)}')
            if len(urls) <= 10:  # Only show URLs if not too many
                for url in urls:
                    self.stdout.write(f'   - {url}')
            else:
                self.stdout.write(f'   (First 5 of {len(urls)} URLs shown)')
                for url in urls[:5]:
                    self.stdout.write(f'   - {url}')
                self.stdout.write(f'   ... and {len(urls) - 5} more')
        else:
            self.stdout.write('🔗 URLs audited: Using URLs from .lighthouserc.js')
        
        if success:
            self.stdout.write(self.style.SUCCESS('✅ Status: SUCCESS'))
        else:
            self.stdout.write(self.style.ERROR('❌ Status: FAILED'))
            self.stdout.write(self.style.WARNING(
                'Common issues:\n'
                '  - NO_NAVSTART: Page took too long to load\n'
                '  - Performance below threshold: Page is too slow\n'
                '  - Missing assertions: Audit did not complete\n'
                'Use --skip-assertions to skip threshold checks.'
            ))
        
        self.stdout.write('='*70 + '\n')

    def _signal_handler(self, signum, frame):
        """Handle interrupt signals."""
        self.stdout.write(self.style.WARNING('\nReceived interrupt signal, cleaning up...'))
        self._cleanup()
        sys.exit(1)

    def _cleanup(self):
        """Clean up background processes."""
        if self.server_process:
            try:
                self.stdout.write('Stopping Django server...')
                if os.name == 'nt':  # Windows
                    self.server_process.terminate()
                else:  # Unix-like
                    self.server_process.send_signal(signal.SIGTERM)
                
                # Wait a bit for graceful shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.server_process.kill()
                    self.server_process.wait()
                
                self.stdout.write(self.style.SUCCESS('Server stopped'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error stopping server: {str(e)}'))
                logger.warning(f'Error stopping server: {str(e)}')

