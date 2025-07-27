from flask import Blueprint, jsonify

bp = Blueprint('settings', __name__)

@bp.route('/settings/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'Settings API is working'})
