# Gamma — wired ✅

Key in `.env` (`GAMMA_API_KEY`), validated 09/07 (auth OK, no credits burned).

- Endpoint: `POST https://public-api.gamma.app/v1.0/generations` — header `X-API-KEY`
- (v0.2 is sunset, returns 410)
- Required: `inputText` (string), `textMode` (`generate` | `condense` | `preserve`)
- Full params: https://developers.gamma.app (format=presentation, themeName, numCards, additionalInstructions, export options)

Plan for the deck (1h timebox, Alex): write the pitch as structured markdown here in the repo (`PITCH.md` → deck script), send with `textMode: preserve` so Gamma renders our exact narrative instead of inventing one, then polish in the Gamma UI. Feeds the "Best use of Gamma" side prize.
