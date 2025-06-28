import re
from django import template
import random

def is_email_verified(email):
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # Match the pattern
    return re.match(pattern, email) is not None

def is_valid_mobile_number(mobile):
    pattern = r'^\+91\s[6-9]\d{9}$'
    return re.match(pattern, mobile) is not None

# def is_valid_password(password):
#     pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
#     return re.match(pattern, password) is not None


def is_valid_password(password):
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r'[@$!%*#?&]', password):
        errors.append("Password must contain at least one special character (@, $, !, %, *, #, ?, &).")

    if len(errors) == 0:
        is_password = True, 
    else:
        is_password = False, ','.join(errors)
    return is_password



# helper.py
import random

def generate_username_suggestions(base_name, count=3):
    suggestions = []
    for _ in range(count):
        number = random.randint(100, 999)
        suggestions.append(f"{base_name}{number}")
    return suggestions
