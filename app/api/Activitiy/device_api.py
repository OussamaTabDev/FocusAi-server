"""
server/app/api/device_bp.py
REST wrapper for core.device_controller.DeviceController
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "core" / "layers"))

from datetime import date
from flask import Blueprint, request, jsonify
from device_controller import DeviceController  # type: ignore
import threading
from app.api.Activitiy import device_controller_bp

bp = device_controller_bp 

_controller = DeviceController()

# ------------------------------------------------------------------
# Timer control
# ------------------------------------------------------------------
@bp.route("/start", methods=["POST"])
def start_timer():
    data = request.get_json(force=True)
    mins  = float(data.get("minutes", 0))
    action = data.get("action", "sleep")
    warn   = data.get("warning", True)
    grace  = float(data.get("grace_seconds", 10))

    def _run():
        _controller._checking_loop(time_limit=mins, action=action,
                                   is_warning=warn, grace_seconds=grace)

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"message": f"Timer started for {mins} min, action={action}"})

@bp.route("/stop", methods=["POST"])
def stop_timer():
    _controller.stop()
    return jsonify({"message": "Timer stopped"})

@bp.route("/status", methods=["GET"])
def status():
    return jsonify({
        "is_timing": _controller.is_timing,
        "elapsed_seconds": _controller.elapsed(),
        "time_limit": _controller.time_limit,
        "action": _controller.action,
        "warning": _controller.is_warning
    })

# ------------------------------------------------------------------
# History
# ------------------------------------------------------------------
@bp.route("/history", methods=["GET"])
def history():
    return jsonify(_controller.history)

@bp.route("/history", methods=["DELETE"])
def clear_history():
    _controller.clear_history()
    return jsonify({"message": "history cleared"})

# ------------------------------------------------------------------
# Pass-code gate
# ------------------------------------------------------------------
@bp.route("/unlock", methods=["POST"])
def unlock():
    body = request.get_json(force=True)
    code = body.get("passcode", "")
    if code == _controller.PASSCODE:
        today = str(date.today())
        if today in _controller.history:
            _controller.history[today]["requires_passcode"] = False
            _controller._save_history()
        return jsonify({"success": True})
    return jsonify({"success": False}), 403

@bp.route("/passcode", methods=["GET"])
def get_passcode():
    # Usually you would NOT expose this; only for debugging
    return jsonify({"passcode": _controller.PASSCODE})

# ------------------------------------------------------------------
# Immediate power / notifications
# ------------------------------------------------------------------
@bp.route("/power-action", methods=["POST"])
def power_action():
    data = request.get_json(force=True)
    action = data["action"]  # sleep, shutdown, reboot, hibernate, logoff
    delay  = float(data.get("delay", 0))
    _controller.power_action(action, delay)
    return jsonify({"message": f"{action} scheduled in {delay}s"})

@bp.route("/notify", methods=["POST"])
def notify():
    body = request.get_json(force=True)
    _controller._notify(body["title"], body["message"])
    return jsonify({"message": "notification sent"})