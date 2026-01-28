/**
 * Lighthouse CI Configuration
 * 
 * This configuration defines which URLs to audit and the performance
 * budgets/thresholds that must be met for the audits to pass.
 */

// Build collect configuration with optional authentication
const collectConfig = {
  url: [
        // Public pages
        'http://localhost:8000/',
        'http://localhost:8000/editais/',
        'http://localhost:8000/login/',
        'http://localhost:8000/register/',
        'http://localhost:8000/ambientes-inovacao/',
        'http://localhost:8000/startups/',
        'http://localhost:8000/password-reset/',
        'http://localhost:8000/password-reset/done/',
        'http://localhost:8000/password-reset-complete/',
        // Dashboard pages (require authentication - use --all-pages with run_lighthouse command)
        'http://localhost:8000/dashboard/',
        'http://localhost:8000/dashboard/home/',
        'http://localhost:8000/dashboard/editais/',
        'http://localhost:8000/dashboard/editais/novo/',
        'http://localhost:8000/dashboard/startups/',
        'http://localhost:8000/dashboard/startups/submeter/',
        'http://localhost:8000/dashboard/usuarios/',
        // NOTE: /dashboard/avaliacoes/ and /dashboard/relatorios/ removed - these endpoints don't exist
        // Admin pages excluded from Lighthouse CI scanning
        // CRUD pages (require authentication)
        'http://localhost:8000/cadastrar/',
      ],
      numberOfRuns: parseInt(process.env.LHCI_NUMBER_OF_RUNS || '3', 10),
      // Chrome flags for headless mode (array format for better compatibility)
      chromeFlags: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
      ],
      // Wait for page to be fully loaded
      settings: {
        maxWaitForFcp: 60000,  // Increased from 30s to 60s
        maxWaitForLoad: 120000,  // Increased from 60s to 120s
        skipAudits: [],
      },
      // Increase protocol timeout to handle slow page loads (in milliseconds)
      // This fixes "Page.navigate timed out" errors
      // Set via puppeteerLaunchOptions for proper Chrome connection timeout handling
      puppeteerLaunchOptions: {
        protocolTimeout: 180000,  // 180 seconds (3 minutes)
      },
      // Server will be started manually in GitHub Actions workflow
      // This ensures proper server startup and readiness before Lighthouse runs
      // Authentication cookie will be added via extraHeaders if AUTH_COOKIE env var is set
      // This prevents redirects and allows testing of protected pages
};

// Add authentication cookie if provided via environment variable
if (process.env.AUTH_COOKIE) {
  collectConfig.extraHeaders = {
    'Cookie': process.env.AUTH_COOKIE
  };
}

module.exports = {
  ci: {
    collect: collectConfig,
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
        // SEO thresholds (0-100) - apply only to non-admin URLs
        // Admin pages don't need SEO checks, so we exclude them using matchingUrlPattern
        'categories:seo': [
          'error',
          {
            minScore: parseFloat(process.env.LHCI_SEO_THRESHOLD || '0.90'),
            matchingUrlPattern: '^(?!.*/admin/).*$', // Negative lookahead: exclude URLs containing /admin/
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

