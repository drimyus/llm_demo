import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.conf import settings

from .validators import validate_inputs
from .services.llm import generate_brief


@require_POST
@ratelimit(key='ip', rate='10/m', block=True)
def generate_brief_endpoint(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    brand = (payload.get('brand') or '').strip()
    platform = (payload.get('platform') or '').strip()
    goal = (payload.get('goal') or '').strip()
    tone = (payload.get('tone') or '').strip()

    errors = validate_inputs(brand, platform, goal, tone)
    if errors:
        return JsonResponse({"errors": errors}, status=400)

    try:
        result = generate_brief(brand, platform, goal, tone)
        return JsonResponse({
            "brief": result.brief,
            "angles": result.angles,
            "criteria": result.criteria,
            "metrics": {
                "latency_ms": result.latency_ms,
                "usage": result.usage,
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@ensure_csrf_cookie
def home(request):
    model_name = getattr(settings, 'GROQ_MODEL', os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'))
    return render(request, 'index.html', {"model_name": model_name})
