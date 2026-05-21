from flask import Blueprint

bp = Blueprint('caregiver', __name__)

from app.caregiver import routes
