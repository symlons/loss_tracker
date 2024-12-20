import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production';
  
  return {
    plugins: [react()],
    server: {
      proxy: {
        "/api": {
          target: isProduction 
            ? "http://167.235.139.154/"
            : "http://localhost:5005",
          changeOrigin: true,
          secure: isProduction,
          // Only rewrite in development mode
          rewrite: isProduction 
            ? undefined 
            : (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
