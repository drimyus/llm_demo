# Collabstr AI Brief Generator

A minimal Django app that generates a short influencer campaign brief using a local LLM via Ollama. It demonstrates clean orchestration, prompt design, guardrails, and basic telemetry, with a Collabstr‑adjacent single‑page UI.

## Screenshot
![AI Brief Generator UI](docs/screenshot.png)

## Tech Stack
- **Backend**: Django 5, `django-ratelimit`, simple validators
- **LLM**: `langchain-ollama` with an Ollama model (default: `phi3`)
- **Frontend**: HTML/CSS/JS + jQuery

## Project Structure
- `collabstr_ai/` – Django project (settings, urls)
- `brief/` – App with API endpoint, templates, and static assets
  - `views.py` – `generate_brief_endpoint()` and `home()`
  - `services/llm.py` – Ollama LLM call and JSON parsing + latency metrics
  - `validators.py` – Input validation + profanity filter
  - `templates/index.html` – Single‑page UI
  - `static/js/app.js` – jQuery AJAX + rendering
  - `static/css/style.css` – Collabstr‑adjacent light theme (Inter font, gradient CTA)

## Setup
1. Install dependencies (uv recommended):
   ```bash
   uv sync
   ```
  
2. Ensure Ollama is installed and running, and pull your model if needed:
   ```bash
   ollama pull phi3
   ```
3. Environment (optional; defaults shown):
   - `OLLAMA_MODEL=phi3`
   - `OLLAMA_BASE_URL=http://localhost:11434`
4. Initialize DB and run:
   ```bash
   uv run python manage.py migrate
   uv run python manage.py runserver 0.0.0.0:8000
   # If port 8000 is taken, use 8001
   ```

## API
- POST ` /api/generate_brief`
  Request JSON:
  ```json
  {
    "brand": "Acme Skincare",
    "platform": "Instagram|TikTok|UGC",
    "goal": "Awareness|Conversions|Content Assets",
    "tone": "Professional|Friendly|Playful"
  }
  ```
  Response JSON:
  ```json
  {
    "brief": "...4–6 sentences...",
    "angles": ["...", "...", "..."],
    "criteria": ["...", "...", "..."],
    "metrics": {
      "latency_ms": 1234,
      "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }
  }
  ```

## Prompt Design Choices
- **System prompt** (`brief/services/llm.py::SYSTEM_PROMPT`):
  - Enforces: 4–6 sentence concise brief; then 3 content angles; then 3 creator criteria.
  - “Avoid fluff; tailor to inputs.”
- **User prompt**: compact, built from the four inputs; requests a single JSON object with `brief`, `angles`, `criteria`.
- **Determinism**: temperature set to 0.3 and output constrained to JSON; angles/criteria clamped to three items server‑side for stability.

## Guardrails Implemented
- **Input validation** (`brief/validators.py`):
  - Allowlists for `platform`, `goal`, `tone`.
  - Brand required and basic profanity filter.
- **Rate‑limiting**: `@django_ratelimit.decorators.ratelimit(key='ip', rate='10/m', block=True)`.
- **Generation limits**: `num_predict=500`, `temperature=0.3` in the Ollama client.
- **Server‑side validation** of parsed JSON, with safe fallbacks.

## Metrics: Tokens and Latency
- **Latency**: measured around the LLM call using `time.perf_counter()`; returned as `metrics.latency_ms`.
- **Token usage**: Ollama via LangChain doesn’t consistently expose token counts; we return zeros to keep the shape stable.
- **Frontend**: renders latency and (placeholder) token metrics in the result card.

## Frontend Behavior
- Single page (`/`) with 4 inputs and a Generate button.
- On submit: disables button, shows loading, sends AJAX to `/api/generate_brief` with CSRF header.
- Renders:
  - Brief paragraph (4–6 sentences)
  - 3 numbered content angles
  - 3 bulleted creator selection criteria
  - Metrics (latency and token placeholders)

## Styling Notes
- Collabstr‑adjacent light theme: Inter font, soft borders, subtle shadows, gradient primary button.
- Styles live in `brief/static/css/style.css`. Typography is loaded via Google Fonts in `templates/index.html`.
- You can refine colors and spacing to match assets under `tmp/` if desired.

## Deploy
- Any Django‑friendly host works (Render, Railway, Fly.io, a VM, etc.).
- Set `DJANGO_SECRET_KEY` and `ALLOWED_HOSTS` appropriately.
- Ensure the Ollama server is reachable from the app (or host it alongside the app).

## Deliverables Checklist
- Public GitHub repo link
- README (this file) with:
  - Prompt design choices
  - Guardrails
  - How tokens/latency are measured
  - Short Loom demo (< 1 minute) of the feature
- A live, public webpage URL to test the generator

## Quick Troubleshooting
- Port in use: run server on `0.0.0.0:8001`.
- CSRF errors: ensure you loaded `/` first so the CSRF cookie is set; AJAX sends `X‑CSRFToken`.
- Ollama errors: confirm `ollama serve` is running and the model exists (`ollama pull phi3`).
