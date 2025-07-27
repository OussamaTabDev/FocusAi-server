from flask import Blueprint, jsonify

bp = Blueprint('user', __name__)

@bp.route('/user/ping', methods=['GET'])
def ping():
    return jsonify({'message': 'User API is working'})
