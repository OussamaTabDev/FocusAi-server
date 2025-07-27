from flask import Blueprint

widgets_bp  = Blueprint("widgets" , __name__ , url_prefix="/api/widgets")



# routes register 
from . import system_stats_api
from . import weather_api