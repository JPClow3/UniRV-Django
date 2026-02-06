/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{css,js}",
    "../../templates/**/*.html",
    // If you render Tailwind class names from JS, add specific files here.
  ],
  theme: {
    extend: {
      colors: {
        // Primary brand colors - modernized palette
        primary: "#2563EB",       // Bright blue (updated from #27348b)
        secondary: "#22c55e",     // Green for agro (unchanged)
        darkblue: "#1e3a8a",      // Deep blue for hero/footer

        // Legacy aliases for backward compatibility
        unirvBlue: "#2563EB",     // Maps to new primary
        agrohubBlue: "#1d4ed8",   // Hover state blue
        agrohubGreen: "#22c55e",  // Same as secondary

        // Surface colors
        "background-light": "#F8FAFC",
        "surface-light": "#FFFFFF",
        "surface-dark": "#1E293B",

        // Text colors
        "text-light": "#1E293B",
        "text-muted": "#64748B",
      },
      fontFamily: {
        display: ["Montserrat", "sans-serif"],
        body: ["Inter", "Montserrat", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "0.5rem",
        lg: "1rem",
        xl: "1.5rem",
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
    // New design system colors
    "bg-primary",
    "bg-primary-hover",
    "bg-darkblue",
    "bg-secondary",
    "text-primary",
    "text-primary-hover",
    "text-secondary",
    "border-primary",
    "border-primary-hover",
    "border-secondary",
  ],
};

