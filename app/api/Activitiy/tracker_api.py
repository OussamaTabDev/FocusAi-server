"""
server/app/api/tracker_api.py
Routes for tracker_bp
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import jsonify, request, send_file
from app.api.Activitiy import tracker_bp                    # already created in __init__.py
from tracker import WindowTracker                 # type: ignore
import threading

_tracker = WindowTracker(interval=1, session_gap_seconds=30)

def _ensure_tracker_started():
    if not _tracker.is_tracking:
        _tracker.start()

# --------------------------------------------------------------
# Attach routes to the existing blueprint
# --------------------------------------------------------------
@tracker_bp.route("/status", methods=["GET"])
def status():
    return jsonify({"is_tracking": _tracker.is_tracking, "interval": _tracker.interval})

@tracker_bp.route("/start", methods=["POST"])
def start():
    _ensure_tracker_started()
    return jsonify({"message": "started"})

@tracker_bp.route("/stop", methods=["POST"])
def stop():
    _tracker.stop()
    return jsonify({"message": "stopped"})

@tracker_bp.route("/current", methods=["GET"])
def current():
    info = _tracker.get_current_window()
    return jsonify(info.__dict__) if info else ("", 404)

@tracker_bp.route("/history", methods=["GET"])
def history():
    _ensure_tracker_started()
    hist = _tracker.history.get_raw_history()
    return jsonify([h.__dict__ for h in hist])

@tracker_bp.route("/sessions", methods=["GET"])
def sessions():
    _ensure_tracker_started()
    sess = _tracker.history.get_sessions()
    for s in sess:
        s["windows"] = [w.__dict__ for w in s["windows"]]
    return jsonify(sess)

@tracker_bp.route("/screenshot", methods=["GET"])
def screenshot():
    _ensure_tracker_started()
    raw = request.args.get("raw") == "1"
    img = _tracker.capturer.capture_active_window()
    if img is None:
        return ("", 404)
    if raw:
        from io import BytesIO
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return send_file(buf, mimetype="image/png")
    import tempfile, os
    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    img.save(tmp, "PNG")
    return send_file(tmp, as_attachment=True, download_name="screenshot.png")

@tracker_bp.route("/interval" , methods=["POST"])
def set_interval():
    body = request.get_json(silent=True)
    print("body: " , body)
    if not body or "interval" not in body:
        return jsonify({"error": "JSON body must contain 'interval'"}), 400
    
    _tracker.interval = int(body["interval"])
    ok = _tracker.interval == int(body["interval"])
    return (jsonify({"message": "modified"}), 201) if ok else (jsonify({"error": "exists"}), 409)
    