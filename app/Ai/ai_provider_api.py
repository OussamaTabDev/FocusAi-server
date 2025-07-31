"""
server/app/api/ai_bp.py
REST wrapper for core.ai_provider.AIProviderManager
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "core" / "Providers"))

from flask import Blueprint, request, jsonify
from InitAIProvider import AIProviderManager, ProviderType # type: ignore
from app.Ai import ai_provider_bp

bp = ai_provider_bp

_manager = AIProviderManager()

# ------------------------------------------------------------------
# Provider management
# ------------------------------------------------------------------
@bp.route("/providers", methods=["GET"])
def list_providers():
    return jsonify({
        "available": _manager.list_available_providers(),
        "initialized": _manager.list_initialized_providers()
    })

@bp.route("/initialize", methods=["POST"])
def init_provider():
    body = request.get_json(force=True)
    pt   = ProviderType[body["provider"].upper()]
    key  = body["api_key"]
    model = body.get("model")
    retries = body.get("max_retries", 3)
    timeout = body.get("timeout", 30)

    from ai_provider import ProviderConfig  #type: ignore
    cfg = ProviderConfig(
        provider_type=pt,
        api_key=key,
        model_name=model,
        max_retries=retries,
        timeout=timeout
    )
    try:
        _manager.create_provider(cfg)
        _manager.set_default_provider(pt)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@bp.route("/default", methods=["GET"])
def get_default():
    prov = _manager.get_default_provider()
    return jsonify({"default": str(prov) if prov else None})

# ------------------------------------------------------------------
# Classification helper (optional) – reuse ProductivityTracker logic
# ------------------------------------------------------------------
@bp.route("/classify", methods=["POST"])
def classify():
    """
    Quick classification via the active provider.
    Body: {"text": "youtube.com"}
    """
    body = request.get_json(force=True)
    text = body["text"]
    prov = _manager.get_default_provider()
    if not prov:
        return jsonify({"error": "no provider initialized"}), 400
    try:
        category = prov.classify(text)
        return jsonify({"text": text, "category": category})
    except Exception as e:
        return jsonify({"error": str(e)}), 500