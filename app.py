from flask import Flask, render_template, request, redirect, flash
from flask_login import login_required, current_user, LoginManager, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from models import db, Post, MyUser


app = Flask(__name__, static_url_path='/static')
upload_folder = os.path.join('image', 'uploads')
app.config['UPLOAD'] = upload_folder
app.secret_key = os.urandom(24)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return MyUser.select().where(MyUser.id==int(user_id)).first()


@app.before_request
def before_request():
    db.connect()
    
@app.after_request
def after_request(response):
    db.close()
    return response



# @app.route('/', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         file = request.files['img']
#         filename = secure_filename(file.filename)
#         file.save(os.path.join(app.config['UPLOAD'], filename))
#         img = os.path.join(app.config['UPLOAD'], filename)
#         return render_template('image_render.html', img=img)
#     return render_template('image_render.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method=='POST':
        email = request.form['email']
        password = request.form['password']
        user = MyUser.select().where(MyUser.email==email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect('/login/')
        else:
            login_user(user)
            return redirect('/')
    return render_template('login.html')


@app.route('/logout/')
def logout():
    logout_user()
    return redirect('/login/')


def validate_password(password):
    if len(password) < 8:
        return False
    if not re.search("[a-z]", password):
        return False
    if not re.search("[A-Z]", password):
        return False
    if not re.search("[0-9]", password):
        return False
    return True

@app.route('/register/', methods=('GET', 'POST'))
def register():
    if request.method=='POST':
        file = request.files['image']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD'], filename))
        image = os.path.join(app.config['UPLOAD'], filename)
        email = request.form['email']
        username = request.form['username']
        age = request.form['age']
        full_name = request.form['full_name']
        password = request.form['password']
        user = MyUser.select().where(MyUser.email==email).first()
        if user:
            flash('email addres already exists')
            return redirect('/register/')
        if MyUser.select().where(MyUser.username==username).first():
            flash('username already exists')
            return redirect('/register/')
        else:
            if validate_password(password):
                MyUser.create(
                    email=email,
                    username=username,
                    age=age,
                    password=generate_password_hash(password),
                    full_name=full_name,
                    image=image
                )
                return redirect('/login/')
            else:
                flash('wrong password')
                return redirect('/register/')
    return render_template('register.html')


@app.route('/create/', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        Post.create(
            title=title,
            author=current_user,
            content=content
        )
        return redirect('/')
    return render_template('create.html')


@app.route('/<int:id>/')
def get_post(id):
    post = Post.select().where(Post.id==id).first()
    if post:
        return render_template('post_detail.html', post=post)
    return f'Post with id = {id} does not exists'
        

@app.route('/')
def index():
    all_posts = Post.select()
    return render_template('index.html', posts=all_posts)
        

@app.route('/<int:id>/update/', methods=('GET', 'POST'))
@login_required
def update(id):
    post = Post.select().where(Post.id==id).first()
    if request.method == 'POST':
        if post:
            if current_user==post.author:
                title = request.form['title']
                content = request.form['content']
                obj = Post.update({
                    Post.title: title,
                    Post.content: content
                }).where(Post.id==id)
                obj.execute()
                return redirect(f'/{id}/')
            return f'you are not author of this post'
        return f'Post with id = {id} does not exists'
    return render_template('update.html', post=post)


@app.route('/<int:id>/delete/', methods=('GET', 'POST'))
@login_required
def delete(id):
    post = Post.select().where(Post.id==id).first()
    if request.method == 'POST':
        if post:
            if current_user==post.author:
                post.delete_instance()
                return redirect('/')
            return f'you are not author of this post'
        return f'Post with id = {id} does not exists'
    return render_template('delete.html', post=post)


@app.route('/profile/<int:id>/')
def profile(id):
    user = MyUser.select().where(MyUser.id==id).first()
    posts = Post.select().where(Post.author==user)
    return render_template('profile.html', user=user, posts=posts)


@app.route('/current_profile/')
@login_required
def my_profile():
    posts = Post.select().where(Post.author==current_user)
    return render_template('profile.html', user=current_user, posts=posts)
    


if __name__ == '__main__':
    app.run(debug=True)