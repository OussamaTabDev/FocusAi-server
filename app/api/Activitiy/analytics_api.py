"""
server/app/api/analytics_api.py
REST endpoints for SessionAnalytics
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import Blueprint, request, jsonify
# from analytics import SessionAnalytics          # lives in core/
from app.api.Activitiy import tracker_bp, analytics_bp         # reuse the same tracker instance from tracker_api.py

bp = analytics_bp

# ------------------------------------------------------------------
# Obtain analytics object from the already-running tracker
# ------------------------------------------------------------------
from app.api.Activitiy.tracker_api import _tracker
_analytics = _tracker.analytics

# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@bp.route("/app-time", methods=["GET"])
def app_time():
    """GET /api/analytics/app-time?hours=6"""
    hours = request.args.get("hours", type=int)
    return jsonify(_analytics.get_time_by_app(hours))

@bp.route("/window-type-time", methods=["GET"])
def window_type_time():
    return jsonify(_analytics.get_time_by_window_type())

@bp.route("/top-windows", methods=["GET"])
def top_windows():
    n = request.args.get("n", default=5, type=int)
    hours = request.args.get("hours", type=int)
    return jsonify(_analytics.get_top_windows(n, hours))

@bp.route("/productivity-summary", methods=["GET"])
def productivity_summary():
    hours = request.args.get("hours", type=int)
    return jsonify(_analytics.get_productivity_summary(hours))

@bp.route("/productive-apps", methods=["GET"])
def productive_apps():
    hours = request.args.get("hours", type=int)
    return jsonify(_analytics.get_productive_apps_ranking(hours))

@bp.route("/distracting-apps", methods=["GET"])
def distracting_apps():
    hours = request.args.get("hours", type=int)
    return jsonify(_analytics.get_distracting_apps_ranking(hours))

@bp.route("/daily-summary", methods=["GET"])
def daily_summary():
    days = request.args.get("days", default=7, type=int)
    return jsonify(_analytics.get_daily_summary(days))

@bp.route("/weekly-summary", methods=["GET"])
def weekly_summary():
    weeks = request.args.get("weeks", default=4, type=int)
    return jsonify(_analytics.get_weekly_summary(weeks))

@bp.route("/monthly-summary", methods=["GET"])
def monthly_summary():
    months = request.args.get("months", default=6, type=int)
    return jsonify(_analytics.get_monthly_summary(months))