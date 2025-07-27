from app import create_app, db
# from app.tracking.monitor import ActivityMonitor
import threading
import time

app = create_app()

# def start_activity_monitoring():
#     """Start the activity monitoring in a separate thread"""
#     monitor = ActivityMonitor()
#     monitor.start_monitoring()

if __name__ == '__main__':
    # Create database tables
    for rule in app.url_map.iter_rules():
        print(f"Route: {rule} → Endpoint: {rule.endpoint} : {rule.methods}")

    with app.app_context():
        db.create_all()
    
    # Start activity monitoring in background thread
    # monitor_thread = threading.Thread(target=start_activity_monitoring, daemon=True)
    # monitor_thread.start()
    
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=8000)