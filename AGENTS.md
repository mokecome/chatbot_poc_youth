# Repository Guidelines

## Project Structure & Module Organization
- `src/` holds the Vite + React TypeScript UI: `components/` (chat UI, modal, portal demos), `contexts/AuthContext.tsx`, `services/api.ts` for API calls, `styles/` for theme tokens, `assets/` for images, and `guidelines/` for prompt rules.
- `public/` stores static assets bundled by Vite; `dist/` is the build output¡Xdo not edit manually.
- `app.py` is the Flask backend (chat, surveys, sessions); `api/index.py` adapts it for Vercel serverless. Data and uploads live in `app.sqlite3`, `uploads/`, and `rag_data/`.
- Deployment config sits in `vercel.json`; marketing/content assets are under `images/`.

## Build, Test, and Development Commands
- `npm install` then `npm run dev` to start the Vite dev server (defaults to http://localhost:5173).
- `npm run build` emits the production bundle to `dist/`.
- `python -m venv .venv && .\.venv\Scripts\activate && pip install -r requirements.txt` sets up backend dependencies.
- `python app.py` runs the Flask API on port 8300; set `OPENAI_API_KEY`, `POSTGRES_URL`/`POSTGRES_URL_NON_POOLING`, `FRONTEND_ORIGIN`, and `SYSTEM_PROMPT` in `.env` or `.env.local`.
- On Vercel, `/api/*` is routed via `api/index.py`; storage falls back to a tmp directory¡Xkeep uploads small.

## Coding Style & Naming Conventions
- TypeScript-first, functional React components with PascalCase file names; favor hooks for state and context.
- Use 2-space indentation; compose classes with `clsx`/`tailwind-merge` and keep utility strings readable.
- Keep network logic in `src/services/api.ts`; avoid ad hoc fetches inside components.
- Share tokens in `src/styles/hotelTheme.ts`; keep component-specific styles close to the component.

## Testing Guidelines
- No automated suite today¡Xwhen adding tests, prefer small `*.test.tsx`/`*.test.ts` using Vitest + Testing Library.
- Manual checks: run `npm run dev`, exercise chat send/login flows, and hit `POST /api/chat` against the Flask server with sample payloads before shipping.

## Commit & Pull Request Guidelines
- Write concise Conventional Commit-style messages (e.g., `feat: add floating chatbot`, `fix: guard unauthenticated send`).
- PRs should include a short summary, screenshots/GIFs for UI changes, steps to verify locally, and any env/config or schema notes.
- Do not commit secrets or large media; keep `dist/`, `node_modules/`, and local DB files out of PRs.

## Security & Configuration Tips
- Never commit `.env`/`.env.local`; rotate any keys that appear in logs.
- `app.py` writes to `uploads/` and SQLite during local dev¡Xclear test data before sharing. On serverless, ensure writable tmp paths are used.
