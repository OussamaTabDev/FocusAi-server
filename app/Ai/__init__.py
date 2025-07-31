from flask import Blueprint

ai_provider_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

from . import ai_provider_api

# Server/app/api/Activitiy/productivity_api.py


# routes register 
# from . import activity_api
# from . import weather_apiactivity_bp  = Blueprint("activity" , __name__ , url_prefix="/api/activity")
