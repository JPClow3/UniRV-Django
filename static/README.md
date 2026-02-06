# Static Assets Structure

This directory contains static assets for the AgroHub application.

## Directory Layout

```
static/
├── css/                    # Custom CSS files
│   ├── animations.css      # CSS animations (orbit, toast, etc.)
│   ├── detail.css          # Edital detail page styles
│   └── print.css           # Print-specific styles
├── fonts/                  # Self-hosted fonts (Montserrat)
├── img/                    # Images and icons
│   └── hero/               # Hero background images
├── js/                     # JavaScript files
│   ├── main.js             # Core functionality (menu, toast, modals)
│   ├── animations.js       # GSAP-based page animations
│   ├── animations-native.js # CSS/IntersectionObserver animations (fallback)
│   ├── editais-index.js    # Editais listing page logic
│   ├── edital-form.js      # Form handling for editais
│   ├── detail.js           # Detail page functionality
│   └── *.min.js            # Minified versions (production)
└── vendor/                 # Third-party libraries
    ├── fontawesome/        # Font Awesome icons
    └── gsap/               # GSAP animation library
```

## Build Pipeline

The build process is managed by npm scripts in `theme/static_src/`:

```bash
# Full build (CSS + JS + vendor)
cd theme/static_src && npm run build

# Watch mode for development (CSS only)
cd theme/static_src && npm run dev
```

### Build Outputs

| Source | Output | Purpose |
|--------|--------|---------|
| `theme/static_src/src/styles.css` | `theme/static/css/dist/styles.css` | Tailwind CSS |
| `static/js/*.js` | `static/js/*.min.js` | Minified JS |
| `node_modules/@fortawesome` | `static/vendor/fontawesome/` | Font Awesome |
| `node_modules/gsap` | `static/vendor/gsap/` | GSAP library |

## Related Directories

- `theme/static_src/` - Tailwind CSS source and build configuration
- `theme/static/css/dist/` - Compiled Tailwind output
- `staticfiles/` - Django `collectstatic` output (production)

## Adding New JavaScript

1. Create the JS file in `static/js/`
2. Add minification script to `theme/static_src/package.json`
3. Reference in templates using `{% static 'js/filename.js' %}`

## Font Configuration

Fonts are self-hosted to avoid render-blocking external requests:
- `static/fonts/Montserrat-Regular.ttf`
- `static/fonts/Montserrat-SemiBold.ttf`

Font-face declarations are in `theme/static_src/src/styles.css`.
