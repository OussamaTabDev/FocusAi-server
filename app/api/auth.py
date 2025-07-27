from flask import Blueprint, jsonify

bp = Blueprint('auth', __name__)

@bp.route('/auth/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'Auth API is working'})
