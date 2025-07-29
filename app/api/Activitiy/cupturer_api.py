"""
server/app/api/capturer_bp.py
REST wrapper for core.ImageCapturer
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

from flask import Blueprint, request, jsonify, send_file
# from ImageCapturer import ImageCapturer
from app.api.Activitiy.tracker_api import _tracker      # reuse tracker instance

from app.api.Activitiy import cupturer_bp
bp = cupturer_bp

_capturer = _tracker.capturer        # already configured instance

# ------------------------------------------------------------------
# Control capture
# ------------------------------------------------------------------
@bp.route("/start", methods=["POST"])
def start():
    _capturer.start()
    return jsonify({"message": "Image capturing started"})

@bp.route("/stop", methods=["POST"])
def stop():
    _capturer.stop()
    return jsonify({"message": "Image capturing stopped"})

@bp.route("/status", methods=["GET"])
def status():
    return jsonify({
        "is_capturing": _capturer.is_capturing,
        "interval_sec": _capturer.interval,
        "latest_time": _capturer.capture_time
    })

# ------------------------------------------------------------------
# History & cleanup
# ------------------------------------------------------------------
@bp.route("/history", methods=["GET"])
def history():
    """
    Return in-memory history (timestamps + filenames).
    For full file download use /download.
    """
    with _capturer.lock:
        return jsonify([
            {"timestamp": t, "filepath": fp}
            for t, _, fp in _capturer.image_history
        ])

@bp.route("/clear-memory", methods=["POST"])
def clear_memory():
    _capturer.clear_history()
    return jsonify({"message": "in-memory history cleared"})

@bp.route("/clean-storage", methods=["POST"])
def clean_storage():
    body = request.get_json(silent=True) or {}
    days_old = body.get("days_old", _capturer.auto_cleanup_days)
    specific_month = body.get("specific_month")
    specific_day   = body.get("specific_day")
    _capturer.clean_storage(days_old, specific_month, specific_day)
    return jsonify({"message": "storage cleaned"})

# ------------------------------------------------------------------
# File download
# ------------------------------------------------------------------
@bp.route("/download/<path:filename>")
def download(filename):
    """Download a specific screenshot file by relative path."""
    filepath = Path(_capturer.base_folder) / filename
    if not filepath.exists():
        return jsonify({"error": "file not found"}), 404
    return send_file(filepath, as_attachment=True)

# ------------------------------------------------------------------
# Storage info
# ------------------------------------------------------------------
@bp.route("/storage-info", methods=["GET"])
def storage_info():
    return jsonify({"info": _capturer.get_storage_info()})

# ------------------------------------------------------------------
# Capture image manually  
# ------------------------------------------------------------------
@bp.route("interval" , methods=["POST"])
def set_interval():
    body = request.get_json(silent=True) or {}
    interval = body.get("interval", _capturer.interval)
    _capturer.set_interval(interval)
    return jsonify({"message": f"Capture interval set to {interval} seconds"})