/**
 * Lighthouse CI Configuration
 * 
 * This configuration defines which URLs to audit and the performance
 * budgets/thresholds that must be met for the audits to pass.
 */

module.exports = {
  ci: {
    collect: {
      url: [
        // Public pages
        'http://localhost:7000/',
        'http://localhost:7000/editais/',
        'http://localhost:7000/login/',
        'http://localhost:7000/register/',
        'http://localhost:7000/ambientes-inovacao/',
        'http://localhost:7000/projetos-aprovados/',
        'http://localhost:7000/startups/',
        'http://localhost:7000/health/',
        'http://localhost:7000/password-reset/',
        'http://localhost:7000/password-reset/done/',
        'http://localhost:7000/password-reset-complete/',
        // Dashboard pages (require authentication - use --all-pages with run_lighthouse command)
        'http://localhost:7000/dashboard/',
        'http://localhost:7000/dashboard/home/',
        'http://localhost:7000/dashboard/editais/',
        'http://localhost:7000/dashboard/editais/novo/',
        'http://localhost:7000/dashboard/projetos/',
        'http://localhost:7000/dashboard/projetos/submeter/',
        'http://localhost:7000/dashboard/avaliacoes/',
        'http://localhost:7000/dashboard/usuarios/',
        'http://localhost:7000/dashboard/relatorios/',
        // Admin (requires authentication)
        'http://localhost:7000/admin/',
        // CRUD pages (require authentication)
        'http://localhost:7000/cadastrar/',
      ],
      numberOfRuns: 3,
      // Chrome flags for headless mode
      chromeFlags: '--no-sandbox --disable-setuid-sandbox',
      // Wait for page to be fully loaded
      settings: {
        maxWaitForFcp: 30000,
        maxWaitForLoad: 60000,
        skipAudits: [],
      },
      // Server will be managed automatically by Lighthouse CI
      // Environment variables (DJANGO_SECRET_KEY, DJANGO_DEBUG, ALLOWED_HOSTS) are inherited from the process
      // Note: Migrations and collectstatic should be run before Lighthouse starts (handled in CI workflow)
      startServerCommand: 'python manage.py runserver 127.0.0.1:7000 --noreload',
      // Match Django's runserver output (case-insensitive, matches "Starting development server" or similar)
      startServerReadyPattern: '(?i)(starting development server|development server is running|quit the server)',
      startServerReadyTimeout: 60000,
      // Authentication cookie will be added automatically by run_lighthouse command
      // For manual usage, add: extraHeaders: { 'Cookie': 'sessionid=...' }
    },
    assert: {
      assertions: {
        // Performance thresholds (0-100)
        'categories:performance': [
          'error',
          {
            minScore: parseFloat(process.env.LHCI_PERFORMANCE_THRESHOLD || '0.80'),
          },
        ],
        // Accessibility thresholds (0-100)
        'categories:accessibility': [
          'error',
          {
            minScore: parseFloat(process.env.LHCI_ACCESSIBILITY_THRESHOLD || '0.90'),
          },
        ],
        // Best Practices thresholds (0-100)
        'categories:best-practices': [
          'error',
          {
            minScore: parseFloat(process.env.LHCI_BEST_PRACTICES_THRESHOLD || '0.90'),
          },
        ],
        // SEO thresholds (0-100)
        'categories:seo': [
          'error',
          {
            minScore: parseFloat(process.env.LHCI_SEO_THRESHOLD || '0.90'),
          },
        ],
        // Performance metrics - warn if these are slow
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.1 }],
      },
    },
    upload: {
      target: 'filesystem',
      outputDir: './lighthouse_reports',
      reportFilename: 'lighthouse-results.json',
    },
    server: {
      port: 9001,
      storage: './lighthouse_data',
    },
  },
};

