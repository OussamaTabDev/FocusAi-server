# history_api.py 
"""
server/app/api/history_bp.py
REST endpoints for WindowHistory with database persistence
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

from flask import Blueprint, request, jsonify
from app.api.Activitiy.tracker_api import _tracker              # reuse same tracker instance
from datetime import datetime
from app.api.Activitiy import history_bp 
import logging

bp = history_bp

_history = _tracker.history

# ------------------------------------------------------------------
# Raw history (now with database support)
# ------------------------------------------------------------------
@bp.route("/raw", methods=["GET"])
def raw_history():
    """Get raw window records from memory cache or database."""
    limit = request.args.get("limit", type=int)
    source = request.args.get("source", default="cache")  # "cache" or "database"
    app_name = request.args.get("app")
    
    try:
        if source == "database":
            # Get directly from database
            records = _history.get_raw_history_from_db(limit, app_name)
        else:
            # Get from memory cache (existing behavior)
            records = _history.raw_history[-limit:] if limit else _history.raw_history
            if app_name:
                records = [r for r in records if r.app == app_name]
        
        return jsonify([r.__dict__ for r in records])
    except Exception as e:
        logging.error(f"Error getting raw history: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Sessions (enhanced with database support)
# ------------------------------------------------------------------
@bp.route("/sessions", methods=["GET"])
def sessions():
    """Get sessions from database."""
    hours = request.args.get("hours", type=int)
    period = request.args.get("period")  # "day", "week", "month"
    offset = request.args.get("offset", default=0, type=int)
    
    try:
        if period:
            sess = _history.get_sessions_by_period(period, offset)
        elif hours:
            sess = _history.get_recent_sessions(hours)
        else:
            # Get recent sessions by default
            sess = _history.get_recent_sessions(24)
        
        # Convert dataclass to dict
        return jsonify([
            {
                "session_id": s.session_id,
                "app_name": s.app_name,
                "start_time": s.start_time.isoformat(),
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "total_duration": s.total_duration,
                "duration_minutes": s.duration_minutes,
                "context_changes": s.context_changes,
                "titles_seen": s.titles_seen[-10:],  # Limit titles for API response
                "status_changes": s.status_changes,
                "window_count": s.window_count,
                "is_active": s.is_active
            }
            for s in sess
        ])
    except Exception as e:
        logging.error(f"Error getting sessions: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# App statistics (enhanced with database support)
# ------------------------------------------------------------------
@bp.route("/stats", methods=["GET"])
def stats():
    """Get app statistics from database."""
    app = request.args.get("app")
    
    try:
        stats_data = _history.get_app_statistics(app)
        
        # Convert AppStatistics objects to dict
        result = {}
        for app_name, stat in stats_data.items():
            result[app_name] = {
                "app_name": stat.app_name,
                "total_time": stat.total_time,
                "total_time_hours": stat.total_time / 3600,
                "session_count": stat.session_count,
                "contexts": stat.contexts,
                "statuses": stat.statuses,
                "average_session_duration": stat.average_session_duration,
                "average_session_minutes": stat.average_session_duration / 60,
                "longest_session": stat.longest_session,
                "longest_session_minutes": stat.longest_session / 60,
                "last_used": stat.last_used.isoformat() if stat.last_used else None
            }
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error getting app statistics: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Period summaries (enhanced)
# ------------------------------------------------------------------
@bp.route("/summary", methods=["GET"])
def summary():
    """Get status summary for a specific period."""
    period = request.args.get("period", default="day")
    offset = request.args.get("offset", default=0, type=int)
    
    try:
        summary_data = _history.get_status_summary_by_period(period, offset)
        return jsonify(summary_data)
    except Exception as e:
        logging.error(f"Error getting summary: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/daily", methods=["GET"])
def daily():
    """Get daily summaries."""
    days = request.args.get("days", default=7, type=int)
    
    try:
        daily_data = _history.get_daily_summary_range(days)
        return jsonify(daily_data)
    except Exception as e:
        logging.error(f"Error getting daily summaries: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/weekly", methods=["GET"])
def weekly():
    """Get weekly summaries."""
    weeks = request.args.get("weeks", default=4, type=int)
    
    try:
        weekly_data = _history.get_weekly_summary_range(weeks)
        return jsonify(weekly_data)
    except Exception as e:
        logging.error(f"Error getting weekly summaries: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/monthly", methods=["GET"])
def monthly():
    """Get monthly summaries."""
    months = request.args.get("months", default=6, type=int)
    
    try:
        monthly_data = _history.get_monthly_summary_range(months)
        return jsonify(monthly_data)
    except Exception as e:
        logging.error(f"Error getting monthly summaries: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# App usage and productivity endpoints
# ------------------------------------------------------------------
@bp.route("/usage", methods=["GET"])
def app_usage():
    """Get app usage summary."""
    hours = request.args.get("hours", default=24, type=int)
    period = request.args.get("period")
    offset = request.args.get("offset", default=0, type=int)
    
    try:
        if period:
            usage_data = _history.get_app_usage_by_period(period, offset)
        else:
            usage_data = _history.get_app_usage_summary(hours)
        
        # Convert seconds to hours for better readability
        usage_hours = {app: time_seconds / 3600 for app, time_seconds in usage_data.items()}
        
        return jsonify({
            "usage_seconds": usage_data,
            "usage_hours": usage_hours,
            "period": period or f"{hours} hours",
            "offset": offset
        })
    except Exception as e:
        logging.error(f"Error getting app usage: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/productivity", methods=["GET"])
def productivity():
    """Get productivity summary."""
    hours = request.args.get("hours", default=24, type=int)
    
    try:
        productivity_data = _history.get_productivity_summary(hours)
        
        # Calculate totals and percentages
        total_time = sum(productivity_data.values())
        productivity_percentages = {}
        if total_time > 0:
            for status, time_spent in productivity_data.items():
                productivity_percentages[status] = (time_spent / total_time) * 100
        
        return jsonify({
            "times": productivity_data,
            "percentages": productivity_percentages,
            "total_time": total_time,
            "total_hours": total_time / 3600,
            "hours": hours
        })
    except Exception as e:
        logging.error(f"Error getting productivity data: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/status", methods=["GET"])
def status_summary():
    """Get comprehensive status summary."""
    hours = request.args.get("hours", default=24, type=int)
    
    try:
        status_data = _history.get_status_summary(hours)
        return jsonify(status_data)
    except Exception as e:
        logging.error(f"Error getting status summary: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/rankings/productive", methods=["GET"])
def productive_apps():
    """Get apps ranked by productivity."""
    hours = request.args.get("hours", default=24, type=int)
    
    try:
        rankings = _history.get_productive_apps_ranking(hours)
        
        return jsonify([
            {
                "app": app,
                "productive_time_seconds": productive_time,
                "productive_time_hours": productive_time / 3600,
                "productivity_ratio": ratio,
                "productivity_percentage": ratio * 100
            }
            for app, productive_time, ratio in rankings
        ])
    except Exception as e:
        logging.error(f"Error getting productive apps ranking: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/rankings/distracting", methods=["GET"])
def distracting_apps():
    """Get apps ranked by distraction time."""
    hours = request.args.get("hours", default=24, type=int)
    
    try:
        rankings = _history.get_distracting_apps_ranking(hours)
        
        return jsonify([
            {
                "app": app,
                "distracting_time_seconds": distracting_time,
                "distracting_time_hours": distracting_time / 3600,
                "distraction_ratio": ratio,
                "distraction_percentage": ratio * 100
            }
            for app, distracting_time, ratio in rankings
        ])
    except Exception as e:
        logging.error(f"Error getting distracting apps ranking: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/context/<app_name>", methods=["GET"])
def app_context_breakdown(app_name):
    """Get context breakdown for a specific app."""
    hours = request.args.get("hours", default=24, type=int)
    
    try:
        context_data = _history.get_context_breakdown(app_name, hours)
        
        # Convert to hours and calculate percentages
        total_time = sum(context_data.values())
        context_hours = {ctx: time_sec / 3600 for ctx, time_sec in context_data.items()}
        context_percentages = {}
        if total_time > 0:
            context_percentages = {ctx: (time_sec / total_time) * 100 for ctx, time_sec in context_data.items()}
        
        return jsonify({
            "app_name": app_name,
            "contexts": {
                "times_seconds": context_data,
                "times_hours": context_hours,
                "percentages": context_percentages
            },
            "total_time_seconds": total_time,
            "total_time_hours": total_time / 3600,
            "hours": hours
        })
    except Exception as e:
        logging.error(f"Error getting context breakdown for {app_name}: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Database management endpoints
# ------------------------------------------------------------------
@bp.route("/database/info", methods=["GET"])
def database_info():
    """Get database information."""
    try:
        db_info = _history.get_database_info()
        return jsonify(db_info)
    except Exception as e:
        logging.error(f"Error getting database info: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/database/sync", methods=["POST"])
def sync_database():
    """Sync in-memory cache with database."""
    try:
        _history.sync_cache_with_database()
        return jsonify({"message": "Cache synced with database successfully"})
    except Exception as e:
        logging.error(f"Error syncing cache with database: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/database/backup", methods=["POST"])
def create_backup():
    """Create a database backup."""
    try:
        from database.backup import DatabaseBackup #type: ignore
        from database.config import DatabaseConfig #type: ignore
        
        database_url = DatabaseConfig.get_database_url('production')
        backup = DatabaseBackup(database_url)
        backup_path = backup.create_backup()
        
        if backup_path:
            return jsonify({
                "message": "Backup created successfully",
                "backup_path": backup_path
            })
        else:
            return jsonify({"error": "Failed to create backup"}), 500
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route("/database/cleanup", methods=["POST"])
def cleanup_database():
    """Remove old data from database."""
    data = request.get_json(silent=True, force=True)
    days = data.get("days", 30) if data else 30
    
    try:
        _history.cleanup_old_data(days)
        return jsonify({"message": f"Cleaned data older than {days} days"})
    except Exception as e:
        logging.error(f"Error cleaning up database: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Overall meta stats (enhanced)
# ------------------------------------------------------------------
@bp.route("/meta", methods=["GET"])
def meta():
    """Get overall statistics summary."""
    try:
        meta_data = _history.get_stats_summary()
        return jsonify(meta_data)
    except Exception as e:
        logging.error(f"Error getting meta statistics: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Export/Import endpoints
# ------------------------------------------------------------------
@bp.route("/export", methods=["GET"])
def export_data():
    """Export data for backup or analysis."""
    format_type = request.args.get("format", default="json")  # json, csv
    period = request.args.get("period", default="month")
    offset = request.args.get("offset", default=0, type=int)
    
    try:
        if format_type == "json":
            # Export comprehensive JSON data
            export_data = {
                "sessions": [
                    {
                        "session_id": s.session_id,
                        "app_name": s.app_name,
                        "start_time": s.start_time.isoformat(),
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "total_duration": s.total_duration,
                        "context_changes": s.context_changes,
                        "titles_seen": s.titles_seen,
                        "status_changes": s.status_changes,
                        "window_count": s.window_count
                    }
                    for s in _history.get_sessions_by_period(period, offset)
                ],
                "statistics": {
                    app_name: {
                        "total_time": stat.total_time,
                        "session_count": stat.session_count,
                        "contexts": stat.contexts,
                        "statuses": stat.statuses,
                        "average_session_duration": stat.average_session_duration,
                        "longest_session": stat.longest_session,
                        "last_used": stat.last_used.isoformat() if stat.last_used else None
                    }
                    for app_name, stat in _history.get_app_statistics().items()
                },
                "export_info": {
                    "period": period,
                    "offset": offset,
                    "exported_at": datetime.now().isoformat(),
                    "format": format_type
                }
            }
            
            return jsonify(export_data)
        
        else:
            return jsonify({"error": "CSV export not implemented yet"}), 501
            
    except Exception as e:
        logging.error(f"Error exporting data: {e}")
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
# Health check endpoints
# ------------------------------------------------------------------
@bp.route("/health", methods=["GET"])
def health_check():
    """Health check for the tracking system."""
    try:
        # Check if tracking is active
        is_tracking = _tracker.is_tracking if hasattr(_tracker, 'is_tracking') else False
        
        # Check database connectivity
        db_healthy = True
        try:
            _history.get_database_info()
        except:
            db_healthy = False
        
        # Check current session
        current_session_info = None
        if _history.current_session:
            current_session_info = {
                "app": _history.current_session.app_name,
                "duration_minutes": _history.current_session.duration_minutes,
                "window_count": _history.current_session.window_count
            }
        
        return jsonify({
            "status": "healthy" if (is_tracking and db_healthy) else "unhealthy",
            "tracking_active": is_tracking,
            "database_healthy": db_healthy,
            "current_session": current_session_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error in health check: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500