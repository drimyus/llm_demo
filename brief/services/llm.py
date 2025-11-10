import json
import time
import os
from dataclasses import dataclass
from typing import List, Dict

from django.conf import settings
from groq import Groq


SYSTEM_PROMPT = (
    "You are an assistant that writes concise, production-ready influencer campaign briefs. "
    "Constraints: 4-6 sentence brief; then provide exactly 3 content angles; then exactly 3 creator selection criteria. "
    "Output strictly one JSON object with keys: brief (string), angles (array of 3 strings), criteria (array of 3 strings). "
    "Angles and criteria elements must be plain strings only (no nested JSON/objects/arrays, no markdown, no backticks). "
    "Avoid fluff; tailor to inputs."
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


def _groq_client() -> Groq:
    api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def generate_brief(brand: str, platform: str, goal: str, tone: str) -> BriefResult:
    start = time.perf_counter()
    client = _groq_client()
    model = getattr(settings, 'GROQ_MODEL', os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'))
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"{build_user_prompt(brand, platform, goal, tone)}\n\n"
                "Return exactly this JSON shape and nothing else (no markdown fences):\n"
                "{\n"
                "  \"brief\": \"<4-6 sentence paragraph>\",\n"
                "  \"angles\": [\"<angle string>\", \"<angle string>\", \"<angle string>\"],\n"
                "  \"criteria\": [\"<criteria string>\", \"<criteria string>\", \"<criteria string>\"]\n"
                "}\n"
                "Rules: elements of 'angles' and 'criteria' must be plain strings only (no JSON, no lists, no objects, no colons if avoidable)."
            ),
        },
    ]
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=500,
    )
    latency_ms = int((time.perf_counter() - start) * 1000)

    content = (resp.choices[0].message.content or '') if resp and resp.choices else ''

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

    # Token usage from Groq
    u = getattr(resp, 'usage', None)
    usage = {
        "prompt_tokens": getattr(u, 'prompt_tokens', 0) if u else 0,
        "completion_tokens": getattr(u, 'completion_tokens', 0) if u else 0,
        "total_tokens": getattr(u, 'total_tokens', 0) if u else 0,
    }

    return BriefResult(
        brief=brief,
        angles=angles,
        criteria=criteria,
        latency_ms=latency_ms,
        usage=usage,
    )
