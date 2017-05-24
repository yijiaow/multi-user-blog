from google.appengine.ext import db
from utils import *

class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()
    @classmethod
    def by_id(cls, uid):
        return cls.get_by_id(uid, parent = user_key())
    @classmethod
    def by_name(cls, name):
        u = cls.all().filter('name =', name).get()
        return u
    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return cls(parent = user_key(), name = name, pw_hash = pw_hash, email = email)
    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and check_secure_pw(name, pw, u.pw_hash):
            return u

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    author = db.ReferenceProperty(User)
    created = db.DateTimeProperty(auto_now_add = True) #set to now when object is first created
    last_modified = db.DateTimeProperty(auto_now = True) #set to now when object is saved
    
    likes_counter = db.IntegerProperty(default = 0)
    liked_by = db.ListProperty(int) #set as empty list initially, update as users like post
    btn_txt = db.StringProperty(default = 'Like')

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str('permalink.html', p = self)
    def render_content(self):
        return self.content.replace('\n', '<br>')
    @classmethod
    def by_id(cls, post_id):
        return cls.get_by_id(int(post_id), parent = blog_key())

class Comment(db.Model):
    post_id = db.IntegerProperty(required = True)
    content = db.TextProperty(required = True)
    author = db.ReferenceProperty(User)
    created = db.DateTimeProperty(auto_now_add = True)
    @classmethod
    def by_id(cls, comment_id):
        return cls.get_by_id(int(comment_id))