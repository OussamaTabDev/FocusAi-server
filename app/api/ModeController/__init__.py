from flask import Blueprint

mode_controller_bp = Blueprint('modes', __name__ , url_prefix="/api/modes")

from . import mode_controller_api

# Server/app/api/Activitiy/productivity_api.py


# routes register 
# from . import activity_api
# from . import weather_apiactivity_bp  = Blueprint("activity" , __name__ , url_prefix="/api/activity")
