"""
server/app/api/productivy_api.py
Routes for productivy_bp  (note typo in blueprint name)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import jsonify, request, send_file
from app.api.Activitiy import productivy_bp
from productivity_tracker import ProductivityTracker , ProductivityCategory

_tracker = ProductivityTracker(ai_provider=None)

@productivy_bp.route("/classify/<resource>", methods=["GET"])
def classify(resource: str):
    return jsonify({"resource": resource, "category": _tracker.detect_status(resource)})

@productivy_bp.route("/classify", methods=["POST"])
def classify_bulk():
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return ("Send JSON list", 400)
    return jsonify({r: _tracker.detect_status(r) for r in data})

@productivy_bp.route("/rules", methods=["GET"])
def rules():
    return jsonify(_tracker.config["rules"])

@productivy_bp.route("/rules/<category>", methods=["POST"])
def add_rule(category: str):
    if category not in ProductivityCategory.__args__:
        return ("Invalid category", 400)
    body = request.get_json(silent=True)
    if not body or "resource" not in body:
        return ('{"resource": "..."}', 400)
    _tracker.add_rule(body["resource"], category)
    return jsonify({"message": "added"}), 201

@productivy_bp.route("/overrides", methods=["GET"])
def overrides():
    return jsonify(_tracker.config["user_overrides"])

@productivy_bp.route("/overrides", methods=["POST"])
def add_override():
    body = request.get_json(silent=True)
    if not body or "resource" not in body or "category" not in body:
        return ('{"resource": "...", "category": "..."}', 400)
    if body["category"] not in ProductivityCategory.__args__:
        return ("Invalid category", 400)
    _tracker.add_user_override(body["resource"], body["category"])
    return jsonify({"message": "added"}), 201

@productivy_bp.route("/cache", methods=["GET"])
def cache():
    return jsonify(_tracker.config["ai_cache"])

@productivy_bp.route("/cache/<resource>", methods=["DELETE"])
def clear_cache(resource: str):
    _tracker.config["ai_cache"].pop(resource.lower(), None)
    _tracker._save_config()
    return jsonify({"message": "removed"})

@productivy_bp.route("/stats", methods=["GET"])
def stats():
    return jsonify(_tracker.get_stats())

@productivy_bp.route("/export", methods=["GET"])
def export():
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    _tracker.export_rules(path)
    return send_file(path, as_attachment=True, download_name="productivity_rules.json")

@productivy_bp.route("/import", methods=["POST"])
def import_rules():
    if "file" not in request.files:
        return ("file required", 400)
    f = request.files["file"]
    if not f.filename.endswith(".json"):
        return ("json file required", 400)
    import tempfile, os
    fd, tmp = tempfile.mkstemp()
    os.close(fd)
    f.save(tmp)
    try:
        _tracker.import_rules(tmp)
    finally:
        os.remove(tmp)
    return jsonify({"message": "imported"}), 200