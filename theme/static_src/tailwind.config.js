/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{css,js}",
    "../../templates/**/*.html",
    "../../templates/**/*.js",
    "../../static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        unirvBlue: "#27348b",
        agrohubBlue: "#1d4ed8",
        agrohubGreen: "#22c55e",
      },
    },
  },
  safelist: [
    // Toast background utilities referenced dynamically in templates/JS
    "bg-blue-600",
    "bg-green-600",
    "bg-yellow-500",
    "bg-red-600",
    // Matching text utilities used in toast icons and alerts
    "text-blue-600",
    "text-green-600",
    "text-yellow-600",
    "text-red-600",
  ],
};

