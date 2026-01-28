/**
 * Copy Font Awesome and GSAP from node_modules to static/vendor.
 * Run from theme/static_src: node scripts/copy-vendor.js
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '../../..');
const staticDir = path.join(root, 'static');
const vendorDir = path.join(staticDir, 'vendor');
const nm = path.join(__dirname, '..', 'node_modules');

function mkdirp(dir) {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function copyRecursive(src, dest) {
  mkdirp(dest);
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const e of entries) {
    const s = path.join(src, e.name);
    const d = path.join(dest, e.name);
    if (e.isDirectory()) {
      copyRecursive(s, d);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

function copyFile(src, dest) {
  mkdirp(path.dirname(dest));
  fs.copyFileSync(src, dest);
}

mkdirp(vendorDir);

const faRoot = path.join(nm, '@fortawesome', 'fontawesome-free');
if (fs.existsSync(faRoot)) {
  copyRecursive(path.join(faRoot, 'css'), path.join(vendorDir, 'fontawesome', 'css'));
  copyRecursive(path.join(faRoot, 'webfonts'), path.join(vendorDir, 'fontawesome', 'webfonts'));
  console.log('Copied Font Awesome to static/vendor/fontawesome');
} else {
  console.warn('@fortawesome/fontawesome-free not found. Run npm install.');
}

const gsapDist = path.join(nm, 'gsap', 'dist');
if (fs.existsSync(gsapDist)) {
  const gsapOut = path.join(vendorDir, 'gsap');
  mkdirp(gsapOut);
  copyFile(path.join(gsapDist, 'gsap.min.js'), path.join(gsapOut, 'gsap.min.js'));
  copyFile(path.join(gsapDist, 'ScrollTrigger.min.js'), path.join(gsapOut, 'ScrollTrigger.min.js'));
  console.log('Copied GSAP to static/vendor/gsap');
} else {
  console.warn('gsap not found. Run npm install.');
}
