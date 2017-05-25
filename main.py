from utils import *
from models import User, Post, Comment

import webapp2
import json

class Handler(webapp2.RequestHandler):
    '''Defines basic functions for rendering pages and setting cookies'''
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        '''
        Cookies are set using Set-Cookie HTTP header, sent in an HTTP response
        The server's HTTP response contains the contents of the webpage, 
        but it also instructs the browser to set cookies
        Parameters:
            name: name of cookie
            val: value of cookie, a string consists both value and hashed value
        '''
        cookie_vals = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s = %s; Path = /' % (name, cookie_vals))

    def read_secure_cookie(self, name):
        cookie_vals = self.request.cookies.get(name)
        return cookie_vals and check_secure_val(cookie_vals)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id = ; Path = /')

    def initialize(self, *a, **kw):
        '''
        By default, each instance of the Handler class will have the attributes 
        request, response and app (that's why one can use e.g. self.request.get(); 
        self.request is a request object) because it inherits these attributes from 
        webapp2.RequestHandler. Whenever the handler is called (i.e. when you receive 
        a request for that URL), a new instance is created and initialized with the 
        appropriate values for the attributes.

        The initialize() method is called every time a new instance of NewPost is 
        created (which happens on each http request to the web server) and as you can 
        see it retrieves the user_id from the cookie (if present), retrives the 
        corresponding User from the db and stores it instance variable user (self.user)
        so it can be easily accessed by the rest of the code.
        '''
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        '''
        If uid has any value that evaluates to True, call the method
        User.by_id(int(uid)) and assign the return value (which will be a User object)
        to self.user. If uid has any value that evaluates to False, assign that value 
        to self.user. In that case, it won't even try to call User.by_id(int(uid)).
        '''
        self.user = uid and User.by_id(int(uid))  # assign a User object to self.user

class Register(Handler):
    def get(self):
        self.render('signup-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        password_verify = self.request.get('verify')
        email = self.request.get('email')
        params = dict(username=username, email=email)
        have_error = False
        if valid_username(username):
            user = User.by_name(username)
            if user:
                params['error_username'] = "That user already exists."
                have_error = True
        else:
            params['error_username'] = "That's not a valid username."
            have_error = True
        if not valid_password(password):
            params['error_password'] = "That's not a valid password."
            have_error = True
        elif password != password_verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True
        if have_error:
            self.render('signup-form.html', **params)
        else:
            user = User.register(username, password, email)
            user.put()
            self.login(user)
            self.redirect('/')

class Login(Handler):
    def get(self):
        self.render('login-form.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        user = User.login(username, password) #login() from User class
        if user:
            self.login(user)
            self.redirect('/')
        else:
            error_login = "Invalid login."
            self.render('login-form.html', error_login=error_login)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')

class PostHandler(Handler):
    '''Handle individual post functions: like, unlike'''
    @login_required
    def get(self, post_id):
        post = Post.by_id(post_id)
        if not post:
            return self.error(404)
        comments = db.GqlQuery('SELECT * FROM Comment WHERE post_id = %s ORDER BY created DESC' % int(post_id))
        self.render('post.html', p=post, comments=comments, user=self.user)
    
    @login_required 
    def post(self, post_id):
        post = Post.by_id(post_id)
        if not post:
            return self.error(404)
        message = ''
        if self.user.key().id() == post.author:
            message = 'You cannot like your own post.'
        elif self.user.key().id() in post.liked_by:
            post.likes_counter -= 1
            post.liked_by.remove(self.user.key().id())
            post.btn_txt = 'Like'
            post.put()
        else:
            post.likes_counter += 1
            post.liked_by.append(self.user.key().id())
            post.btn_txt = 'Unlike'
            post.put()
        self.write(json.dumps({'likes_counter': post.likes_counter, 
                                'btn_txt': post.btn_txt,
                                'message': message}))
class NewPost(Handler):
    @login_required
    def get(self):
        self.render('newpost.html', title='Create a new post')

    @login_required
    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')
        error = ''
        if subject and content:
            post = Post(parent=blog_key(), subject=subject, content=content, 
                        author=self.user) 
                      # new post's likes_counter is set to 0 initially
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = 'Please enter both subject and content.'
            self.render('newpost.html', error=error)

class EditPost(Handler):
    '''Handles editing post'''
    @login_required
    def get(self, post_id):
        post = Post.by_id(post_id)
        if not post:
            return self.error(404)
        elif self.user.key().id() != post.author:
            self.write("You don't have access to edit this post.")
        else:
            self.render('editpost.html', p=post)

    @login_required
    def post(self, post_id):
        post = Post.by_id(post_id)
        subject = self.request.get('subject')
        content = self.request.get('content')
        error = ''
        if subject and content:
            # modify the attributes of the object and update existing entity
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = 'Please enter both subject and content.'
            self.render('editpost.html', p=post, error=error)

class DeletePost(Handler):

    @login_required
    def post(self, post_id):
        post = Post.by_id(post_id)
        if not post:
            return self.error(404)
        if self.user.key().id() != post.author:
            message = 'You do not have access to delete this post.'
        else:
            post.delete()
            message = 'This post has been deleted.'
        self.write(json.dumps({'message': message}))

class CommentHandler(Handler):
    '''Create new comment, edit existing comment'''
    @login_required
    def post(self, post_id):
        comm_content = self.request.get('comment')
        cid = self.request.get('comment_id')
        if comm_content:
            if cid:
                comment = Comment.by_id(cid)
                if self.user.key().id() == comment.author:
                    comment.content = comm_content
                    comment.put()
            else:  # when cid does not exist --> create new comment
                new_comment = Comment(post_id=post_id, content=comm_content, 
                                    author=self.user)
                new_comment.put()
                cid = new_comment.key().id()
                self.write(json.dumps({'cid': cid, 'comm_author': self.user.name, 'comm_content': comm_content}))

class DeleteComment(Handler):

    @login_required
    def post(self, post_id):
        cid = self.request.get('comment_id')
        comment = Comment.by_id(cid)
        error = ''
        if not comment:
            return self.error(404)
        elif self.user.key().id() != comment.author:
            error = 'You do not have access to delete this comment.'
        else:
            comment.delete()
        self.write(json.dumps({'error': error}))

class MainPage(Handler):
    def get(self):
        posts = db.GqlQuery('SELECT * FROM Post ORDER BY created DESC')
        self.render('blog.html', posts=posts, user=self.user)

app = webapp2.WSGIApplication([
    ('/', MainPage),    
    ('/register', Register),
    ('/login', Login),
    ('/logout', Logout),
    ('/blog/([0-9]+)', PostHandler),
    ('/blog/newpost', NewPost),
    ('/blog/([0-9]+)/edit', EditPost),
    ('/blog/([0-9]+)/delete', DeletePost),
    ('/blog/([0-9]+)/comment', CommentHandler),
    ('/blog/([0-9]+)/comment/delete', DeleteComment)
], debug=True)
