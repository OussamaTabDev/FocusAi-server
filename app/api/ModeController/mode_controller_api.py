"""
server/app/api/mode_bp.py
REST wrapper for core.mode_controller.ModeController
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core" / "ModeController"))

from flask import Blueprint, abort, request, jsonify
from dateutil import parser as iso_parser  # pip install python-dateutil

from enums import ModeType, StandardSubMode  # type: ignore
from app.api.Activitiy.tracker_api import _tracker
from models import WindowInfo
from app.api.ModeController import mode_controller_bp

# Blueprint --------------------------------------------------------------------
bp = mode_controller_bp
_controller = _tracker.mode_controller


# ------------------------------------------------------------------
# 1) State & info
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
# 2) Switching
# ------------------------------------------------------------------
@bp.route("/switch", methods=["POST"])
def switch():
    """
    POST /api/mode/switch
    Body: { "mode": "STANDARD", "submode": "FOCUS", "focus": "DEEP",
            "custom_settings": {...} }
    """
    body = request.get_json(force=True)
    mode  = ModeType[body["mode"].upper()]
    sub   = StandardSubMode[body["submode"].upper()] if body.get("submode") else None
    focus = body["focus"].upper() if body.get("focus") else None
    custom = body.get("custom_settings")

    ok = _controller.switch_to_mode(mode, sub, focus, custom)
    return jsonify({"success": ok})


# ------------------------------------------------------------------
# 3) Convenience shortcuts
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
    """
    POST /api/mode/focus/deep   (or /light /custom)
    """
    part = focus_type.strip().upper()
    try:
        ft = part
    except KeyError:
        abort(400, description="Unknown focus type")
    ok = _controller.switch_to_focus(ft)
    return jsonify({"success": ok})


# ------------------------------------------------------------------
# 4) Settings CRUD
# ------------------------------------------------------------------
@bp.route("/settings/<mode_key>", methods=["GET"])
def get_settings(mode_key: str):
    settings = _controller.settings_manager.get_mode_setting(mode_key)
    # settings = mc.settings_manager.get_mode_setting(key)
    print(f'settings : ----------')
    # print(f'{}')
    print(f'settings : ----------')
    
    if not settings:
        abort(404)
    return to_json(settings)


@bp.route("/settings/<mode_key>/<setting>", methods=["PUT"])
def update_setting(mode_key: str, setting: str):
    """
    PUT /api/mode/settings/standard_focus_deep/duration
    Body: { "value": 90 }
    """
    body = request.get_json(force=True)
    try:
        _controller.settings_manager.update_mode_setting(mode_key, setting, body["value"])
        return jsonify({"message": "updated"})
    except Exception as e:
        abort(400, description=str(e))


# Full-file replace / patch / backup / delete
@bp.route("/settings/modes/<key>", methods=["PUT"])
def add_mode(key: str):
    body = request.json
    try:
        _controller.settings_manager.add_mode_config(key, body)  # overwrites if exists
    except ValueError as e:
        abort(400, description=str(e))
    return jsonify(message="updated")


@bp.route("/settings/modes/<key>", methods=["PATCH"])
def patch_mode(key: str):
    body = request.json or {}
    for setting, value in body.items():
        try:
            _controller.settings_manager.update_mode_setting(key, setting, value)
        except (ValueError, AttributeError) as e:
            abort(400, description=str(e))
    return jsonify(message="patched")


@bp.route("/settings/modes/<key>/backup", methods=["POST"])
def backup_mode(key: str):
    try:
        path = _controller.settings_manager.backup_settings(
            Path(f"config/backup_{key}_{int(Path().stat().st_mtime)}.json")
        )
    except Exception as e:
        abort(500, description=str(e))
    return jsonify(backup=str(path))


@bp.route("/settings/modes/<key>", methods=["DELETE"])
def delete_mode(key: str):
    try:
        _controller.settings_manager.delete_mode_config(key)
    except ValueError:
        abort(404)
    return jsonify(message="deleted")


# ------------------------------------------------------------------
# 5) Available modes list
# ------------------------------------------------------------------
@bp.route("/modes", methods=["GET"])
def list_modes():
    return jsonify(_controller.settings_manager.list_available_modes())


@bp.route("/focus-modes", methods=["GET"])
def list_focus_modes():
    return jsonify(_controller.settings_manager.list_available_Focus_modes())


# ------------------------------------------------------------------
# 6) Kids-mode timer helpers
# ------------------------------------------------------------------
@bp.route("/timer/start", methods=["POST"])
def start_timer():
    """
    POST /api/mode/timer/start
    Body: { "minutes": 30, "action": "sleep", "warning": false, "grace_seconds": 10 }
    """
    body = request.get_json(force=True)
    mins = float(body.get("minutes", 60))
    action = body.get("action", "sleep")
    warn = bool(body.get("warning", False))
    grace = float(body.get("grace_seconds", 10))

    import threading
    threading.Thread(
        target=_controller.device_controller._checking_loop,
        args=(mins, action, warn, grace),
        daemon=True,
    ).start()
    return jsonify(message=f"Timer started for {mins} min")


@bp.route("/timer/stop", methods=["POST"])
def stop_timer():
    _controller.device_controller.stop()
    return jsonify(message="Timer stopped")


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


# ------------------------------------------------------------------
# 7) System / utilities
# ------------------------------------------------------------------
@bp.route("/shutdown", methods=["POST"])
def shutdown():
    _controller.cleanup()
    return jsonify(message="graceful shutdown initiated"), 200


# ------------------------------------------------------------------
# 8) Enforcement hook
# ------------------------------------------------------------------
def _parse_window_info(data: Dict[str, Any]) -> WindowInfo:
    return WindowInfo(
        app=data["app"],
        window_type=data.get("window_type", "unknown"),
        title=data.get("title", ""),
        status=data.get("status", ""),
    )


@bp.route("/enforce", methods=["POST"])
def enforce_window():
    data = request.json or {}
    wi = _parse_window_info(data)
    _controller.enforce_current_mode(wi)
    return jsonify(status="enforced")


# ------------------------------------------------------------------
# 9) Blocked apps list (dynamically computed)
# ------------------------------------------------------------------
@bp.route("/blocked-apps", methods=["GET"])
def blocked_apps():
    settings = _controller._get_current_mode_settings()
    if not settings:
        return jsonify([])
    return jsonify(settings.blocked_apps)


# ------------------------------------------------------------------
# 10) Analytics
# ------------------------------------------------------------------
@bp.route("/analytics/sessions", methods=["GET"])
def analytics_sessions():
    p = Path("config/focus_sessions.json")
    if not p.exists():
        return jsonify([])
    with p.open() as f:
        return jsonify(json.load(f))


@bp.route("/analytics/sessions/<int:idx>", methods=["GET"])
def single_session(idx: int):
    p = Path("config/focus_sessions.json")
    if not p.exists():
        abort(404)
    with p.open() as f:
        data = json.load(f)
    try:
        return jsonify(data[idx])
    except IndexError:
        abort(404)


@bp.route("/analytics/productivity-score", methods=["GET"])
def productivity_score():
    return jsonify(score=_controller.productivity_score, streak=_controller.focus_streak)


# ------------------------------------------------------------------
# 11) Validation helper
# ------------------------------------------------------------------
@bp.route("/utils/validate", methods=["GET"])
def validate_combination():
    mode_str = request.args.get("mode")
    sub_str = request.args.get("submode")
    focus_str = request.args.get("focus_type")

    try:
        mode = ModeType[mode_str.upper()] if mode_str else None
        sub = StandardSubMode[sub_str.upper()] if sub_str else None
        focus = focus_str.upper() if focus_str else None
    except KeyError:
        return jsonify(valid=False)

    valid = _controller._validate_mode_combination(mode, sub, focus)
    return jsonify(valid=valid)


@bp.route("/utils/reset-to-defaults", methods=["POST"])
def reset_defaults():
    _controller.settings_manager._create_default_configs()
    _controller.settings_manager.load_settings()
    return jsonify(message="defaults restored")

def to_dict(object):
        return {
            "allowed_apps": object.allowed_apps,
            "blocked_apps": object.blocked_apps,
            "minimized_apps": object.minimized_apps,
            "duration": object.duration.total_seconds() if object.duration else None,
            "strict_mode": object.strict_mode,
            "notifications_enabled": object.notifications_enabled,
            "notification_intensity": object.notification_intensity,
            "screen_time_limit": object.screen_time_limit.total_seconds() if object.screen_time_limit else None,
            "productivity_target": object.productivity_target,
            "time_limit": object.time_limit,
            "bedtime_start": object.bedtime_start,
            "bedtime_end": object.bedtime_end,
            "parental_override_required": object.parental_override_required,
            "screen_time_alerts": object.screen_time_alerts,
            "educational_time_bonus": object.educational_time_bonus,
            "achievement_tracking": object.achievement_tracking,
        }

def to_json(object):
    return json.dumps(to_dict(object), indent=4)