import os
import re
from config import Config


def allowed_file(filename):
    if not filename:
        return False
    extension = os.path.splitext(filename)[1].lower().strip('.')
    return extension in Config.ALLOWED_EXTENSIONS


def is_college_email(email):
    return bool(re.match(r'^[^@\s]+@gcet\.edu\.in$', email.strip().lower()))


def allowed_description(description, image_file):
    normalized = (description or '').strip()
    if not normalized:
        return False
    if image_file and image_file.filename:
        return True
    # When no image is provided, require richer text for matching quality.
    return len(normalized) >= 20
