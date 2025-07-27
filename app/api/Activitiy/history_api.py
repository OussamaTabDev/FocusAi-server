"""
server/app/api/history_bp.py
REST endpoints for WindowHistory (sessions, raw records, cleanup, etc.)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import Blueprint, request, jsonify
from app.api.Activitiy.tracker_api import _tracker              # reuse same tracker instance
from datetime import datetime
from app.api.Activitiy import history_bp 


bp = history_bp

_history = _tracker.history

# ------------------------------------------------------------------
# Raw history
# ------------------------------------------------------------------
@bp.route("/raw", methods=["GET"])
def raw_history():
    limit = request.args.get("limit", type=int)
    records = _history.raw_history[-limit:] if limit else _history.raw_history
    return jsonify([r.__dict__ for r in records])

# ------------------------------------------------------------------
# Sessions
# ------------------------------------------------------------------
@bp.route("/sessions", methods=["GET"])
def sessions():
    hours = request.args.get("hours", type=int)
    if hours:
        sess = _history.get_recent_sessions(hours)
    else:
        sess = _history.app_sessions
    # Convert dataclass to dict
    return jsonify([
        {
            "app_name": s.app_name,
            "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "total_duration": s.total_duration,
            "context_changes": s.context_changes,
            "titles_seen": s.titles_seen,
            "status_changes": s.status_changes,
            "window_count": s.window_count,
            "is_active": s.is_active
        }
        for s in sess
    ])

# ------------------------------------------------------------------
# App statistics
# ------------------------------------------------------------------
@bp.route("/stats", methods=["GET"])
def stats():
    app = request.args.get("app")
    return jsonify(_history.get_app_statistics(app))

# ------------------------------------------------------------------
# Period summaries
# ------------------------------------------------------------------
@bp.route("/summary", methods=["GET"])
def summary():
    period = request.args.get("period", default="day")
    offset = request.args.get("offset", default=0, type=int)
    return jsonify(_history.get_status_summary_by_period(period, offset))

@bp.route("/daily", methods=["GET"])
def daily():
    days = request.args.get("days", default=7, type=int)
    return jsonify(_history.get_daily_summary_range(days))

@bp.route("/weekly", methods=["GET"])
def weekly():
    weeks = request.args.get("weeks", default=4, type=int)
    return jsonify(_history.get_weekly_summary_range(weeks))

@bp.route("/monthly", methods=["GET"])
def monthly():
    months = request.args.get("months", default=6, type=int)
    return jsonify(_history.get_monthly_summary_range(months))

# ------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------
@bp.route("/cleanup", methods=["POST"])
def cleanup():
    days = request.get_json(silent=True, force=True).get("days", 30)
    _history.cleanup_old_data(days)
    return jsonify({"message": f"Cleaned data older than {days} days"})

# ------------------------------------------------------------------
# Overall meta stats
# ------------------------------------------------------------------
@bp.route("/meta", methods=["GET"])
def meta():
    return jsonify(_history.get_stats_summary())