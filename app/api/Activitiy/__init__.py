from flask import Blueprint

tracker_bp = Blueprint('tracker', __name__ , url_prefix="/api/tracker")
utils_bp = Blueprint('utils', __name__ , url_prefix="/api/utils")
productivy_bp = Blueprint('productivy', __name__ , url_prefix="/api/productivy")
config_manger_bp = Blueprint('config_manager', __name__ , url_prefix="/api/config")
analytics_bp = Blueprint('analytics', __name__ , url_prefix="/api/analytics")
history_bp = Blueprint('history', __name__ , url_prefix="/api/history")
cupturer_bp = Blueprint("capturer", __name__, url_prefix="/api/capturer")
device_controller_bp = Blueprint("device_controller", __name__, url_prefix="/api/device")

from . import cupturer_api, tracker_api , utils_api , productivity_api , config_manager_api , analytics_api , history_api , device_api

# Server/app/api/Activitiy/productivity_api.py


# routes register 
# from . import activity_api
# from . import weather_apiactivity_bp  = Blueprint("activity" , __name__ , url_prefix="/api/activity")
