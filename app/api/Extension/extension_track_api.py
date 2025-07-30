"""
server/app/api/analytics_api.py
REST endpoints for SessionAnalytics
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "Core"))

import json
from datetime import datetime
import os
from flask import Blueprint, request, jsonify
from extension_tracker import URLTracker         # type: ignore
 
from app.api.Extension import extension_tracker_bp      # reuse the same tracker instance from tracker_api.py

bp = extension_tracker_bp

# Initialize tracker
tracker = URLTracker()

@bp.route('/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'URL Tracker Server is running'})

@bp.route('/track-url', methods=['POST'])
def track_url():
    """Receive URL data from browser extension"""
    try:
        url_data = request.get_json()
        print(f"Received URL data: {url_data}")
        if not url_data or 'url' not in url_data:
            return jsonify({'error': 'Invalid data'}), 400
        
        # Add server timestamp and extract domain
        url_data['server_timestamp'] = datetime.now().isoformat()
        url_data['domain'] = tracker.extract_domain(url_data['url'])
        
        # Save to both JSON and CSV
        json_success = tracker.save_url(url_data)
        # csv_success = tracker.save_to_csv(url_data)
        
        if json_success :
            print(f"Tracked URL: {url_data['url']}")
            return jsonify({
                'status': 'success',
                'message': 'URL tracked successfully',
                'data': url_data
            })
        else:
            return jsonify({'error': 'Failed to save data'}), 500
            
    except Exception as e:
        print(f"Error in track_url: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_stats():
    """Get tracking statistics"""
    return jsonify(tracker.get_stats())

@bp.route('/urls', methods=['GET'])
def get_urls():
    """Get all tracked URLs"""
    try:
        with open(tracker.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Optional: Filter by date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date or end_date:
            filtered_data = []
            for item in data:
                item_date = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
                if start_date and item_date < datetime.fromisoformat(start_date):
                    continue
                if end_date and item_date > datetime.fromisoformat(end_date):
                    continue
                filtered_data.append(item)
            data = filtered_data
        
        return jsonify({
            'urls': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/export', methods=['GET'])
def export_data():
    """Export data in different formats"""
    export_format = request.args.get('format', 'json')
    
    try:
        if export_format == 'csv':
            with open(tracker.csv_file, 'r', encoding='utf-8') as f:
                csv_data = f.read()
            return csv_data, 200, {'Content-Type': 'text/csv'}
        else:
            with open(tracker.data_file, 'r', encoding='utf-8') as f:
                json_data = f.read()
            return json_data, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({'error': str(e)}), 500


import requests
import time

def close_tabs_by_domain(domain: str):
    """
    Send command to browser extension to close tabs for a specific domain
    """
    try:
        # Clean the domain (remove protocol, www, etc.)
        clean_domain = domain.lower().replace('https://', '').replace('http://', '').replace('www.', '')
        if '/' in clean_domain:
            clean_domain = clean_domain.split('/')[0]
        
        print(f"Attempting to close tabs for domain: {clean_domain}")
        
        # Send command to extension via the server endpoint
        response = requests.post("http://localhost:8000/extension-command", 
                               json={
                                   "action": "closeTabsByDomain",
                                   "domain": clean_domain
                               },
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Extension response: {result}")
            return result
        else:
            print(f"Server responded with status {response.status_code}: {response.text}")
            return {"success": False, "error": f"Server error: {response.status_code}"}
            
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure the Flask server is running on localhost:8000")
        return {"success": False, "error": "Connection refused - server not running"}
    except requests.exceptions.Timeout:
        print("Request timed out")
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        print(f"Error closing tabs: {e}")
        return {"success": False, "error": str(e)}

# Add this endpoint to your Flask server
@bp.route('/extension-command', methods=['POST'])
def extension_command():
    """
    Relay commands to the browser extension
    This acts as a bridge between Python and the browser extension
    """
    try:
        command_data = request.get_json()
        
        if not command_data:
            return jsonify({'error': 'No command data provided'}), 400
        
        print(f"Received extension command: {command_data}")
        
        # Save command for extension to poll
        if save_command_for_extension(command_data):
            return jsonify({
                'success': True,
                'message': 'Command saved for extension',
                'command': command_data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save command'
            }), 500
        
    except Exception as e:
        print(f"Error in extension_command: {e}")
        return jsonify({'error': str(e)}), 500

# Alternative approach: Save commands to a file for extension to poll
def save_command_for_extension(command_data):
    """Save command to a file that the extension can poll"""
    import json
    import os
    
    commands_file = 'config/server/extension_commands.json'
    
    try:
        # Load existing commands
        if os.path.exists(commands_file):
            with open(commands_file, 'r') as f:
                commands = json.load(f)
        else:
            commands = []
        
        # Add timestamp
        command_data['timestamp'] = datetime.now().isoformat()
        command_data['id'] = str(time.time())
        
        commands.append(command_data)
        
        # Keep only last 100 commands
        if len(commands) > 100:
            commands = commands[-100:]
        
        # Save back to file
        with open(commands_file, 'w') as f:
            json.dump(commands, f, indent=2)
        
        return True
    except Exception as e:
        print(f"Error saving command: {e}")
        return False

@bp.route('/get-commands', methods=['GET'])
def get_commands():
    """Get pending commands for the extension"""
    try:
        commands_file = 'config/server/extension_commands.json'
        
        if not os.path.exists(commands_file):
            return jsonify({'commands': []})
        
        with open(commands_file, 'r') as f:
            commands = json.load(f)
        
        return jsonify({'commands': commands})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/clear-commands', methods=['POST'])
def clear_commands():
    """Clear processed commands"""
    try:
        commands_file = 'config/server/extension_commands.json'
        
        if os.path.exists(commands_file):
            os.remove(commands_file)
        
        return jsonify({'success': True, 'message': 'Commands cleared'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
