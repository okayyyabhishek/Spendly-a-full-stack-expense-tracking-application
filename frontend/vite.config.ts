import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/Spendly-a-full-stack-expense-tracking-application/',
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
})
