import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskblog import app, db, bcrypt, mail
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm, Input_textForm, Edit_words   
from flaskblog.models import User, Post, Texts, Sent, Words, Tags
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message 
import nltk
from nltk.tokenize import sent_tokenize
from flaskblog.italian_resources import tools_ita

labels = [
    'JAN', 'FEB', 'MAR', 'APR',
    'MAY', 'JUN', 'JUL', 'AUG',
    'SEP', 'OCT', 'NOV', 'DEC'
]

values = [
    967.67, 1190.89, 1079.75, 1349.19,
    2328.91, 2504.28, 2873.83, 4764.87,
    4349.29, 6458.30, 9907, 16297
]

colors = [
    "#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA",
    "#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1",
    "#C71585", "#FF4500", "#FEDCBA", "#46BFBD"]


@app.route("/")
@app.route("/home")
def home(): 
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='Input text')  
    

@app.route("/input_text", methods=['GET', 'POST'])
def input_text():
    form = Input_textForm()
    if form.validate_on_submit():
        text = Texts(title=form.title.data, text=form.text.data)
        db.session.add(text)
        # for i in (sent_tokenize(text.text)):
        #     sent = Sent(sentence=i, owner_id=text.id)
        #     db.session.add(sent)
        db.session.commit()
        last = Texts.query.order_by(Texts.id.desc()).first()
        for i in (sent_tokenize(last.text)):
            sent = Sent(sentence=i, owner_id=last.id)
            db.session.add(sent)
            db.session.commit()
            # last_sent = Sent.query.order_by(Sent.id.desc()).first()
            tokens_pos =([tools_ita.perc_tagger.tag(tools_ita.tokenizza(sent)) for sent in tools_ita.sent_tokenizza(i)])
            for item in tokens_pos[0]:
                token = item[0]
                pos = item[1]
                word = Words(word=token, pos=pos, sentowner_id=sent.id)
                db.session.add(word)
                db.session.commit()
            
        flash('You insert a text!', 'succes')
        return redirect(url_for('view_text'))
    return render_template('input_text.html', title='Input text', form=form, legend='Input text')

@app.route("/view_text", methods=['GET', 'POST'])
def view_text():
    texts = Texts.query.order_by(Texts.id.desc())
    return render_template('view_text.html', title='Input text', texts=texts, legend='View text')

@app.route("/view_text/<int:texts_id>", methods=['GET', 'POST'])
def sent(texts_id):
    text = Texts.query.get_or_404(texts_id)
    sent = Sent.query.filter_by(owner=text)
    return render_template('sent.html', title=text.title, text=text, sent=sent)

@app.route("/view_words/<int:sent_id>", methods=['GET', 'POST'])
def words(sent_id):
    sent = Sent.query.get_or_404(sent_id)
    words = Words.query.filter_by(sentowner=sent)
    text = Texts.query.filter_by(id=sent.owner_id)
    # text = Texts.query.filter_by(id=sent.owner_id)
    # print(text)
    return render_template('words.html', sent=sent, words=words, text=text)

@app.route("/edit_words/<int:sent_id>", methods=['GET', 'POST'])
def edit_words(sent_id):
    sent = Sent.query.get_or_404(sent_id)
    words = Words.query.filter_by(sentowner=sent)
    text = Texts.query.filter_by(id=sent.owner_id)
    form = Edit_words()
    return render_template('edit_words.html', title='Words', sent=sent, words=words, form=form, text=text)

@app.route("/edit_words/<int:words_id>/update", methods=['GET', 'POST'])
def update_pos(words_id):
    words = Words.query.get_or_404(words_id)
    form = Edit_words()
    if form.validate_on_submit(): 
        print(words.word)
        words.pos = form.edit.data
        db.session.commit()
        flash('Pos has been updated!', 'success')
        return redirect(url_for('edit_words', words_id=words.id, sent_id=words.sentowner.id))
    elif request.method == 'GET':
        form.edit.data = words.pos
    return render_template('edit_words.html', title='Words', sent=sent, words=words, form=form)


@app.route("/view_text/<int:texts_id>/delete", methods=['POST'])
@login_required
def delete_text(texts_id):
    text = Texts.query.get_or_404(texts_id)
    db.session.delete(text)
    db.session.commit()
    return redirect(url_for('view_text'))
    flash('Your text has been deleted!', 'success')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your Account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'succes')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New post', form=form, legend='New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update post', form=form, legend='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))
    flash('Your post has been deleted!', 'success')

@app.route("/user/<string:username>")
def user_posts(username): 
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts=posts, user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='noreply@demo.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form) 


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)