"""
server/app/api/config_bp.py
Routes for runtime configuration management (process map, categories, prefixes, urls).
Register this blueprint in your main app factory.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import Blueprint, request, jsonify
from config_manager import ( # type: ignore
    load_process_map,
    add_or_update_mapping,
    get_all_categories,
    create_category,
    delete_category,
    add_pattern_to_category,
    remove_pattern_from_category,
    get_all_prefixes,
    add_prefix,
    remove_prefix,
    get_all_urls
) 
from app.api.Activitiy import config_manger_bp
bp = config_manger_bp

# ----------------------------------------------------------
# 1. Process Map
# ----------------------------------------------------------
@bp.route("/process-map", methods=["GET"])
def get_map():
    return jsonify(load_process_map())

@bp.route("/process-map", methods=["POST"])
def upsert_map():
    """Body: {"exe": "chrome.exe", "friendly": "Google Chrome"}"""
    data = request.get_json(silent=True)
    if not data or "exe" not in data or "friendly" not in data:
        return jsonify({"error": "JSON body must contain 'exe' and 'friendly'"}), 400
    add_or_update_mapping(data["exe"], data["friendly"])
    return jsonify({"message": "updated"}), 201

# ----------------------------------------------------------
# 2. Categories
# ----------------------------------------------------------
@bp.route("/categories", methods=["GET"])
def list_categories():
    return jsonify(get_all_categories())

@bp.route("/categories", methods=["POST"])
def new_category():
    name = request.get_json(silent=True, force=True)
    if not name or "name" not in name:
        return jsonify({"error": "JSON body must contain 'name'"}), 400
    ok = create_category(name["name"])
    return (jsonify({"message": "created"}), 201) if ok else (jsonify({"error": "exists"}), 409)

@bp.route("/categories/<string:cat>", methods=["DELETE"])
def remove_category(cat):
    ok = delete_category(cat)
    return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

@bp.route("/categories/<string:cat>/patterns", methods=["POST"])
def add_pattern(cat):
    body = request.get_json(silent=True)
    if not body or "pattern" not in body:
        return jsonify({"error": "JSON body must contain 'pattern'"}), 400
    ok = add_pattern_to_category(cat, body["pattern"])
    return (jsonify({"message": "added"}), 201) if ok else (jsonify({"error": "category or pattern issue"}), 400)

@bp.route("/categories/<string:cat>/patterns/<string:pattern>", methods=["DELETE"])
def remove_pattern(cat, pattern):
    ok = remove_pattern_from_category(cat, pattern)
    return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

# ----------------------------------------------------------
# 3. Prefixes
# ----------------------------------------------------------
@bp.route("/prefixes", methods=["GET"])
def list_prefixes():
    return jsonify(get_all_prefixes())

@bp.route("/prefixes", methods=["POST"])
def add_pre():
    body = request.get_json(silent=True)
    if not body or "prefix" not in body:
        return jsonify({"error": "JSON body must contain 'prefix'"}), 400
    ok = add_prefix(body["prefix"])
    return (jsonify({"message": "added"}), 201) if ok else (jsonify({"error": "exists"}), 409)

@bp.route("/prefixes/<string:prefix>", methods=["DELETE"])
def remove_pre(prefix):
    ok = remove_prefix(prefix)
    return ("", 204) if ok else (jsonify({"error": "not found"}), 404)

# ----------------------------------------------------------
# 4. URL history (read-only for now)
# ----------------------------------------------------------
@bp.route("/urls", methods=["GET"])
def list_urls():
    return jsonify(get_all_urls())