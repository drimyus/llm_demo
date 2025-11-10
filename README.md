# Collabstr AI Brief Generator

A minimal Django app that generates a short influencer campaign brief using a hosted LLM via Groq (configurable model). It demonstrates clean orchestration, prompt design, light guardrails, and telemetry, with a Collabstr‑adjacent single‑page UI.

## Screenshot
![AI Brief Generator UI](docs/screenshot.png)

## Demo
- Loom (under 1 minute): https://www.loom.com/share/0927157d1c154456b6e7bb7d44b75f64

## Tech Stack
- **Backend**: Django 5
- **LLM**: Groq API (`GROQ_MODEL` default: `llama-3.1-8b-instant`)
- **Frontend**: HTML/CSS/JS + jQuery

## Project Structure
- `collabstr_ai/` – Django project (settings, urls)
- `brief/` – App with API endpoint, templates, and static assets
  - `views.py` – `generate_brief_endpoint()` and `home()`
  - `services/llm.py` – Groq chat completion call and JSON parsing + latency metrics
  - `validators.py` – Input validation + profanity filter
  - `templates/index.html` – Single‑page UI
  - `static/js/app.js` – jQuery AJAX + rendering
  - `static/css/style.css` – Collabstr‑adjacent light theme (Inter font, gradient CTA)

## Setup (Local)
1. Install dependencies (uv or pip):
   ```bash
   # uv
   uv sync
   # or pip
   pip install -r requirements.txt
   ```

2. Create `.env` (see `.example.env`) with at least:
   ```env
   GROQ_API_KEY=your_groq_key
   GROQ_MODEL=llama-3.1-8b-instant
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
   CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8001,http://localhost:8001,http://0.0.0.0:8001
   ```

3. Initialize DB and run:
   ```bash
   uv run python manage.py migrate
   uv run python manage.py runserver 0.0.0.0:8001
   # Open http://127.0.0.1:8001
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
- **Role and goals**: Acts as an expert strategist/copywriter; invents a plausible product if brand is ambiguous; professional/strategic tone.
- **Brief paragraph**: Single 4–6 sentence paragraph starting with “Here is the campaign brief for [Brand Name].” Must include goal, platform, inferred audience, tone execution, and a quoted key message/CTA.
- **Angles (3)**: Platform‑specific ideas as plain strings formatted “Title — 1–2 sentence description”. Tailored to platform (Reels/Carousels/Stories for Instagram; trends/sounds/challenges for TikTok; prompts/incentives for UGC).
- **Criteria (3)**: Short, actionable strings covering audience demographics, aesthetic/tone alignment, and performance/platform metric.
- **Strict output**: Returns one JSON object only: `brief` (string), `angles` (3 strings), `criteria` (3 strings). No markdown, no nested JSON.

## Guardrails Implemented
- **Input validation** (`brief/validators.py`): allowlists for `platform`, `goal`, `tone`; brand required; basic profanity filter.
- **Rate‑limiting** (`brief/views.py`): `@ratelimit(key='ip', rate='10/m', block=True)`.
- **Strict prompting** (`brief/services/llm.py`): explicit JSON schema; plain‑string enforcement for angles/criteria; no markdown fences.
- **Parsing hardening**:
  - Backend: tolerant JSON extraction, schema clamping to 3 items.
  - Frontend (`brief/static/js/app.js`): strips code fences, attempts JSON recovery, and normalizes display.
- **CSRF**: standard Django CSRF cookie and header usage in AJAX.

## Metrics: Tokens and Latency
- **Latency**: measured around the LLM call using `time.perf_counter()`; returned as `metrics.latency_ms`.
- **Token usage**: populated from Groq’s response (`prompt_tokens`, `completion_tokens`, `total_tokens`).
- **Frontend**: renders latency and token metrics in the result card.

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
- Live demo: https://drimyus.pythonanywhere.com/
- Host options: PythonAnywhere (free), Hugging Face Spaces (Docker), Render/Railway/Fly (credit card may be required).
- Required env vars in production:
  - `DJANGO_SETTINGS_MODULE=collabstr_ai.settings`
  - `DEBUG=False`
  - `ALLOWED_HOSTS=<your-domain>` and `CSRF_TRUSTED_ORIGINS=https://<your-domain>`
  - `DJANGO_SECRET_KEY=<random-strong-secret>`
  - `GROQ_API_KEY=<your_key>` and optional `GROQ_MODEL`

### PythonAnywhere (summary)
1. Bash console:
   ```bash
   git clone https://github.com/<you>/<repo>.git
   cd <repo>
   python3 -m venv ~/.virtualenvs/llm-demo
   source ~/.virtualenvs/llm-demo/bin/activate
   pip install -r requirements.txt
   python manage.py collectstatic --noinput
   python manage.py migrate
   ```
2. Web tab:
   - Manual config (Python 3.x)
   - Virtualenv: `~/.virtualenvs/llm-demo`
   - WSGI: point to `collabstr_ai.wsgi`
   - Static: map `/static/` → `/home/<you>/<repo>/staticfiles`
   - Environment: set variables listed above
   - Reload and open your domain

## Deliverables Checklist
- Public GitHub repo link
- README (this file) with:
  - Prompt design choices
  - Guardrails
  - How tokens/latency are measured
  - Short Loom demo (< 1 minute): https://www.loom.com/share/0927157d1c154456b6e7bb7d44b75f64
- A live, public webpage URL to test the generator

## Quick Troubleshooting
- **Port in use**: run server on `0.0.0.0:8001`.
- **Bad Request (400)**: ensure `ALLOWED_HOSTS` includes your host and visit via `http://127.0.0.1:8001` in dev.
- **CSRF errors**: ensure you loaded `/` first so the CSRF cookie is set; AJAX sends `X‑CSRFToken`.
- **Groq errors**: check `GROQ_API_KEY` and network access.
