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

@tracker_bp.route("/interval", methods=["POST"])
def set_interval():
    body = request.get_json(silent=True)
    print("body: ", body)
    if not body or "interval" not in body:
        return jsonify({"error": "JSON body must contain 'interval'"}), 400
    
    _tracker.interval = int(body["interval"])
    ok = _tracker.interval == int(body["interval"])
    return (jsonify({"message": "modified"}), 201) if ok else (jsonify({"error": "exists"}), 409)


@tracker_bp.route("/restart", methods=["POST"])
def quick_restart():
    """
    Performs a full restart of the WindowTracker to reload all components and configurations.
    """
    try:
        _tracker.quick_restart()
        return jsonify({
            "message": "WindowTracker restarted successfully",
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Restart failed: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/reload-config", methods=["POST"])
def reload_config():
    """
    Reloads configuration files without performing a full restart.
    """
    try:
        _tracker.reload_config_files()
        return jsonify({
            "message": "Configuration files reloaded successfully",
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Config reload failed: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/status", methods=["GET"])
def get_restart_status():
    """
    Returns the current status of all WindowTracker components.
    """
    try:
        status = _tracker.get_restart_status()
        return jsonify({
            "status": "success",
            "data": status
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to get status: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/restart-with-interval", methods=["POST"])
def restart_with_interval():
    """
    Updates the interval and performs a restart in one operation.
    """
    body = request.get_json(silent=True)
    
    try:
        # Update interval if provided
        if body and "interval" in body:
            new_interval = int(body["interval"])
            _tracker.interval = new_interval
            
        # Perform restart
        _tracker.quick_restart()
        
        return jsonify({
            "message": "WindowTracker restarted with new settings",
            "status": "success",
            "interval": _tracker.interval
        }), 200
        
    except ValueError as e:
        return jsonify({
            "error": "Invalid interval value",
            "status": "error"
        }), 400
    except Exception as e:
        return jsonify({
            "error": f"Restart failed: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/health", methods=["GET"])
def health_check():
    """
    Quick health check to see if the tracker is running properly.
    """
    try:
        current_window = _tracker.get_current_window()
        is_tracking = _tracker.is_tracking
        
        return jsonify({
            "status": "success",
            "data": {
                "is_tracking": is_tracking,
                "has_current_window": current_window is not None,
                "current_app": current_window.app if current_window else None,
                "uptime_check": "healthy"
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Health check failed: {str(e)}",
            "status": "error"
        }), 500

@tracker_bp.route("/shutdown", methods=["POST"])
def shutdown_tracker():
    """
    Performs a complete shutdown of the WindowTracker and all its components.
    Saves all data before shutting down.
    """
    try:
        _tracker.shutdown()
        return jsonify({
            "message": "WindowTracker shutdown completed successfully",
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Shutdown failed: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/emergency-shutdown", methods=["POST"])
def emergency_shutdown_tracker():
    """
    Performs an emergency shutdown that forces termination of all processes.
    Use only when normal shutdown fails.
    """
    try:
        _tracker.emergency_shutdown()
        return jsonify({
            "message": "Emergency shutdown completed",
            "status": "success"
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Emergency shutdown failed: {str(e)}",
            "status": "error"
        }), 500


@tracker_bp.route("/shutdown-status", methods=["GET"])
def get_shutdown_status():
    """
    Returns the current shutdown status to verify completion.
    """
    try:
        status = _tracker.get_shutdown_status()
        return jsonify({
            "status": "success",
            "data": status
        }), 200
    except Exception as e:
        return jsonify({
            "error": f"Failed to get shutdown status: {str(e)}",
            "status": "error"
        }), 500







@tracker_bp.route("/force-stop", methods=["POST"])
def force_stop():
    """
    Force stops all tracking and saves data, but keeps components alive.
    Combination of stop + data saving without full shutdown.
    """
    try:
        # Stop tracking
        _tracker.stop()
        
        # Save data like in shutdown but don't clear components
        if hasattr(_tracker, 'history') and _tracker.history:
            if hasattr(_tracker.history, 'save_session'):
                _tracker.history.save_session()
                
        if hasattr(_tracker, 'analytics') and _tracker.analytics:
            if hasattr(_tracker.analytics, 'save_analytics'):
                _tracker.analytics.save_analytics()
        
        return jsonify({
            "message": "Tracking force stopped and data saved",
            "status": "success",
            "is_tracking": _tracker.is_tracking
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Force stop failed: {str(e)}",
            "status": "error"
        }), 500


# Optional: Add a route to shutdown the entire Flask app
@tracker_bp.route("/shutdown-app", methods=["POST"])
def shutdown_app():
    """
    Shuts down the WindowTracker and then the entire Flask application.
    WARNING: This will terminate the entire program!
    """
    try:
        # First shutdown the tracker
        _tracker.shutdown()
        
        # Schedule Flask app shutdown
        def shutdown_server():
            import time
            time.sleep(1)  # Give time for response to be sent
            import os
            os._exit(0)  # Force exit the entire program
        
        # Run shutdown in a separate thread so response can be sent
        import threading
        shutdown_thread = threading.Thread(target=shutdown_server)
        shutdown_thread.daemon = True
        shutdown_thread.start()
        
        return jsonify({
            "message": "Application shutting down...",
            "status": "success"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"App shutdown failed: {str(e)}",
            "status": "error"
        }), 500