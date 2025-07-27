from flask import Blueprint

extension_tracker_bp = Blueprint('e-tracker', __name__ , url_prefix="/e-tracker")



from . import extension_track_api 
# Server/app/api/Activitiy/productivity_api.py


# routes register 
# from . import activity_api
# from . import weather_apiactivity_bp  = Blueprint("activity" , __name__ , url_prefix="/api/activity")
