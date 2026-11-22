# Cloudflare TMDB proxy

This Worker is an optional, fixed-upstream HTTPS relay for the Local Media Client. It only forwards requests to:

- `/3/*` → `https://api.themoviedb.org/3/*`
- `/image/t/p/*` → `https://image.tmdb.org/t/p/*`
- `/health` → local health response

It is **not** an arbitrary URL proxy. The TMDB Read Access Token remains in the app's OS secure storage and is forwarded as a Bearer header only to the fixed TMDB API origin. The Worker has no token secret to configure.

## Deploy

From this directory, with Node.js available:

```sh
npx wrangler@latest login
npx wrangler@latest deploy
```

Wrangler prints the deployed `workers.dev` URL, for example
`https://local-media-tmdb-proxy.<your-subdomain>.workers.dev`.

Smoke-test the public health endpoint:

```sh
curl -i https://local-media-tmdb-proxy.<your-subdomain>.workers.dev/health
```

Then open Local Media Client → Settings → Metadata and paste that **origin URL only** into “TMDB HTTPS proxy address”, save, and tap “Test connection”. Do not append `/3` or `/image`.

## Notes

- HTTPS is required by the app.
- The Worker allows CORS for native app and desktop clients.
- API responses are marked `no-store`; poster and backdrop responses may be cached for one day.
- Only GET/HEAD and CORS preflight are supported.
- A successful `/health` check confirms that the Worker is deployed, not that TMDB itself is reachable. The app's “Test connection” button verifies the TMDB API path and token.
