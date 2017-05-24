import os
import re
import random
import hashlib
import hmac
from string import letters

import jinja2

from google.appengine.ext import db

SECRET = 'fishbreasts'
template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                                     autoescape = True)
def render_str(template, **params):
    '''This returns the rendered template as unicode string'''
    t = jinja_environment.get_template(template)
    return t.render(params)

def valid_username(username):
    USER_RE = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
    return USER_RE.match(username)

def valid_password(password):
    PASS_RE = re.compile(r'^.{3,20}$')
    return PASS_RE.match(password)

def valid_email(email):
    EMAIL_RE = re.compile(r'^[\S]+@[\S]+.[\S]+$')
    return not email or EMAIL_RE.match(email)

def make_secure_val(val):
    # We have replaced the comma, ',' in the cookie value with the pipe,'|'
    # This is because Google App Engine has issue with commas in cookies
    return '%s|%s' % (val, hmac.new(SECRET, val).hexdigest())

def check_secure_val(vals):
    val = vals.split('|')[0]
    if vals == make_secure_val(val):
        return val

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in range(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name+pw+salt).hexdigest()
    return '%s|%s' % (salt, h)

def check_secure_pw(name, pw_entered, pw_vals):
    salt = pw_vals.split('|')[0]
    return pw_vals == make_pw_hash(name, pw_entered, salt)

def user_key(group = 'default'):
    return db.Key.from_path('users', group)

def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)

def login_required(func):
    '''A decorator to confirm a user is logged in or redirect as needed'''
    def check_login(self, *args, **kwargs):
        if not self.user:
            return self.redirect('/login')
        else:
            func(self, *args, **kwargs)
    return check_login
