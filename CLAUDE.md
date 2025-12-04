# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a chatbot POC (Proof of Concept) for Taoyuan City Youth Affairs Bureau (桃園市政府青年事務局). It features a floating chat widget built with React/Vite that communicates with a Flask backend powered by OpenAI.

## Development Commands

```bash
npm install        # Install frontend dependencies
npm run dev        # Start Vite dev server
npm run build      # Build frontend to dist/
```

For backend development:
```bash
pip install -r requirements.txt  # If requirements.txt exists, otherwise install: flask flask-cors openai sqlalchemy python-dotenv
python app.py                    # Run Flask server on port 8300
```

## Architecture

### Frontend (React/Vite)
- **Entry point**: `src/main.tsx` → `src/App.tsx`
- **Main component**: `src/components/FloatingChatbot.tsx` - draggable, resizable chat window with minimize/maximize
- **API layer**: `src/services/api.ts` - `ChatAPI` class handles SSE streaming from `/api/chat`
- **UI components**: `src/components/ui/` - shadcn/ui components with Radix primitives
- **Styling**: Tailwind CSS with custom hotel theme in `src/styles/hotelTheme.ts`

### Backend (Flask)
- **Main app**: `app.py` - Flask server with SQLAlchemy
- **Vercel entry**: `api/index.py` - imports and exposes `app` for Vercel serverless
- **Database**: SQLite locally, Postgres on Vercel (auto-detected via `POSTGRES_URL`)
- **Chat endpoint**: `POST /api/chat` - streams SSE responses with `text`, `end`, `error` event types
- **Survey system**: Routes for dynamic survey forms (`/survey/form`, `/__survey_load`, `/__survey_submit`)

### Streaming Protocol
The chat uses Server-Sent Events (SSE) with JSON payloads:
```json
{"type": "text", "content": "...", "session_id": "..."}
{"type": "end", "content": "", "session_id": "..."}
{"type": "error", "content": "...", "session_id": "..."}
```

## Environment Variables

Required for production:
- `OPENAI_API_KEY` - OpenAI API key (backend will return fallback message if missing)
- `POSTGRES_URL` or `POSTGRES_URL_NON_POOLING` - Vercel Postgres connection string

Optional:
- `VITE_API_BASE_URL` - Frontend API base URL (empty for same-origin)
- `OPENAI_MODEL` - Model to use (default: `gpt-4o-mini`)
- `SYSTEM_PROMPT` - Custom system prompt (default is 桃園青年局 knowledge base)
- `FRONTEND_ORIGIN` - CORS origin (default: `*`)
- `FLASK_DEBUG` - Enable Flask debug mode

## Deployment (Vercel)

- `vercel.json` routes `/api/*` to `api/index.py`
- Build command: `npm run build`
- Output directory: `dist`
- Python runtime handles Flask as serverless function

## Key Patterns

- Chat sessions are persisted to database with message history (last 12 messages used as context)
- Frontend manages streaming state with placeholder messages that get updated as chunks arrive
- `FixedPositionPortal` component ensures fixed positioning works correctly in nested contexts
- The chatbot uses RAG (Retrieval-Augmented Generation) via `rag_gemini.py` to dynamically inject relevant knowledge base content
- `SYSTEM_PROMPT` in `app.py` defines the AI's role, behavior rules, and response format (桃園市青年局智慧客服)
