"""
server/app/api/mode_bp.py
REST wrapper for core.mode_controller.ModeController
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core" / "ModeController"))

from flask import Blueprint, request, jsonify
# from mode_controller import ModeController  # type: ignore
from enums import ModeType, StandardSubMode, FocusType   # type: ignore
from app.api.Activitiy.tracker_api import _tracker 
from app.api.ModeController import mode_controller_bp
bp = mode_controller_bp

_controller = _tracker.mode_controller

# ------------------------------------------------------------------
# State & info
# ------------------------------------------------------------------
@bp.route("/status", methods=["GET"])
def status():
    mode, sub, focus = _controller.get_current_state()
    session = _controller.get_session_duration()
    return jsonify({
        "mode": mode.name,
        "submode": sub.name if sub else None,
        "focus_type": focus.name if focus else None,
        "is_active": _controller.is_active,
        "session_duration_seconds": session.total_seconds() if session else None
    })

# ------------------------------------------------------------------
# Mode switching
# ------------------------------------------------------------------
@bp.route("/switch", methods=["POST"])
def switch():
    body = request.get_json(force=True)
    mode = ModeType[body["mode"].upper()]
    sub  = StandardSubMode[body["submode"].upper()] if body.get("submode") else None
    focus = FocusType[body["focus"].upper()] if body.get("focus") else None
    custom = body.get("custom_settings")

    ok = _controller.switch_to_mode(mode, sub, focus, custom)
    return jsonify({"success": ok})

# ------------------------------------------------------------------
# Convenience shortcuts
# ------------------------------------------------------------------
@bp.route("/standard/normal", methods=["POST"])
def standard_normal():
    ok = _controller.switch_to_standard_normal()
    return jsonify({"success": ok})


@bp.route("/kids", methods=["POST"])
def kids_mode():
    ok = _controller.switch_to_kids_mode()
    return jsonify({"success": ok})

@bp.route("/focus/<focus_type>", methods=["POST"])
def focus_mode(focus_type: str):
    part = [part.strip() for part in focus_type.split("_") if part.strip()][0]
    ok = _controller.switch_to_focus(FocusType[part.upper()])
    return jsonify({"success": ok})
# ------------------------------------------------------------------
# Settings retrieval & update
# ------------------------------------------------------------------
@bp.route("/settings/<mode_key>", methods=["GET"])
def get_settings(mode_key: str):
    settings = _controller.settings_manager.get_mode_setting(mode_key)
    if not settings:
        return jsonify({"error": "not found"}), 404
    return jsonify(settings.__dict__)

@bp.route("/settings/<mode_key>/<setting>", methods=["PUT"])
def update_setting(mode_key: str, setting: str):
    body = request.get_json(force=True)
    new_value = body["value"]
    try:
        _controller.settings_manager.update_mode_setting(mode_key, setting, new_value)
        return jsonify({"message": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ------------------------------------------------------------------
# Available modes
# ------------------------------------------------------------------
@bp.route("/modes", methods=["GET"])
def list_modes():
    return jsonify(_controller.settings_manager.list_available_modes())

@bp.route("/focus_modes", methods=["GET"])
def list_foucs_modes():
    return jsonify(_controller.settings_manager.list_available_Focus_modes())


# ------------------------------------------------------------------
# Timer (kids-mode time-limit) endpoints
# ------------------------------------------------------------------
@bp.route("/timer/start", methods=["POST"])
def start_timer():
    """Start kids-mode timer via REST."""
    body = request.get_json(force=True)
    mins   = float(body.get("minutes", 60))
    action = body.get("action", "sleep")
    warn   = body.get("warning", False)
    grace  = float(body.get("grace_seconds", 10))

    import threading
    threading.Thread(
        target=_controller.device_controller._checking_loop,
        args=(mins, action, warn, grace),
        daemon=True
    ).start()
    return jsonify({"message": f"Timer started for {mins} min"})

@bp.route("/timer/stop", methods=["POST"])
def stop_timer():
    _controller.device_controller.stop()
    return jsonify({"message": "Timer stopped"})

@bp.route("/timer/status", methods=["GET"])
def timer_status():
    dc = _controller.device_controller
    return jsonify({
        "is_timing": dc.is_timing,
        "elapsed_seconds": dc.elapsed(),
        "time_limit": dc.time_limit,
        "action": dc.action,
        "warning": dc.is_warning
    })