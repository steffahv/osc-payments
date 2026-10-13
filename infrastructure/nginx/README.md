# Production proxy - pending

The current Compose configuration is for local development only. In production,
Nginx will serve the output of `npm run build` and proxy `/api` to FastAPI.
Confirm the domain, TLS, and corporate environment before creating the final
configuration. Do not use the Vite development server as a public server.
