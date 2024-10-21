import tailwindcss from 'tailwindcss';
import autoprefixer from 'autoprefixer';

export default {
  content: ["./src/**/*.{html,js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [tailwindcss, autoprefixer],
};

