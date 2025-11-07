import json
import time
from dataclasses import dataclass
from typing import List, Dict

from django.conf import settings
from langchain_ollama import ChatOllama


SYSTEM_PROMPT = (
    "You are an assistant that writes concise, production-ready influencer campaign briefs. "
    "Follow constraints: 4-6 sentences, short, actionable; then 3 numbered content angles; "
    "then 3 bullet creator selection criteria. Avoid fluff; tailor to inputs."
)


@dataclass
class BriefResult:
    brief: str
    angles: List[str]
    criteria: List[str]
    latency_ms: int
    usage: Dict[str, int]


def build_user_prompt(brand: str, platform: str, goal: str, tone: str) -> str:
    return (
        f"Brand: {brand}\n"
        f"Platform: {platform}\n"
        f"Goal: {goal}\n"
        f"Tone: {tone}\n"
        "Output a single compact JSON object with keys: brief, angles, criteria. \n"
        "- brief: 4-6 sentences paragraph tailored to brand, platform, goal, tone.\n"
        "- angles: array of exactly 3 distinct content angles.\n"
        "- criteria: array of exactly 3 creator selection bullets."
    )


def _ollama() -> ChatOllama:
    model = getattr(settings, 'OLLAMA_MODEL', 'phi3')
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    # Pass options directly to the ChatOllama constructor (avoids passing unsupported kwargs)
    return ChatOllama(model=model, base_url=base_url, temperature=0.3, num_predict=500)


def generate_brief(brand: str, platform: str, goal: str, tone: str) -> BriefResult:
    start = time.perf_counter()

    llm = _ollama()
    prompt = (
        f"System:\n{SYSTEM_PROMPT}\n\n"
        f"User:\n{build_user_prompt(brand, platform, goal, tone)}\n\n"
        "Only output valid JSON with keys: brief, angles, criteria."
    )
    # Invoke and capture text
    reply = llm.invoke(prompt)
    latency_ms = int((time.perf_counter() - start) * 1000)

    content = getattr(reply, 'content', '') or ''

    def _strip_code_fences(txt: str) -> str:
        t = (txt or '').strip()
        if t.startswith('```'):
            # remove opening fence with optional language
            first_nl = t.find('\n')
            if first_nl != -1:
                t = t[first_nl+1:]
            if t.endswith('```'):
                t = t[:-3]
        return t.strip()

    def _parse_maybe_json(txt: str):
        # direct parse
        try:
            return json.loads(txt)
        except Exception:
            pass
        # extract first top-level brace region
        try:
            si = txt.index('{')
            ei = txt.rindex('}') + 1
            return json.loads(txt[si:ei])
        except Exception:
            return None

    cleaned = _strip_code_fences(content)
    data = _parse_maybe_json(cleaned)
    if data is None:
        data = {"brief": cleaned, "angles": [], "criteria": []}

    # Basic schema normalization
    brief = str(data.get('brief', '')).strip()
    angles = [str(x).strip() for x in (data.get('angles') or [])][:3]
    criteria = [str(x).strip() for x in (data.get('criteria') or [])][:3]

    # Ollama via LangChain doesn't consistently expose token usage; set zeros
    usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    return BriefResult(
        brief=brief,
        angles=angles,
        criteria=criteria,
        latency_ms=latency_ms,
        usage=usage,
    )
