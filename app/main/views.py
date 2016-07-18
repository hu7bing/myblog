from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app,session
from flask.ext.login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import Permission, Role, User, Post, Tag, Category, Comment
from ..decorators import admin_required
from ..tagcloud import TagCloud
from ..decorators import admin_required, permission_required



@main.route('/', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items

    Cloud=TagCloud(4,6)
    no_notice = 1

    #cate = Category.query.filter_by(posts.category_id.name).first()



    #name = ['PYTHON','Database','UDP','html/css','Unix/Linux','others']
    cate = Post.category_id
    #cate = Category.query.filter_by(name = "PYTHON").first()
    return render_template('index.html',  posts=posts,
                        #form=form,
                           pagination=pagination,
                           show_followed=show_followed,
                           #tagsname=session.get('tagsname'),
                           Cloud = Cloud,Tag = Tag,
                           Category = Category,
                           cate = cate,
                           Post = Post,
                           no_notice = no_notice,
                           )


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination,Post=Post)


@main.route('/tags/<tagname>')
def tags(tagname):

    #posts = Post.query.filter_by(tagname).all()
    tag = Tag.query.filter_by(name=tagname).first()
    posts = tag.posts.all()
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    #posts = pagination.items

    Cloud=TagCloud(1,10)

    #name = ['PYTHON','Database','UDP','html/css','Unix/Linux','others']
    cate = Post.category_id
    #cate = Post.category_id

    return render_template('index.html',  posts=posts,
                        #form=form,
                           pagination=pagination,
                           #tagsname=session.get('tagsname'),
                           Cloud = Cloud,Tag = Tag,
                           cate = cate
                           )


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username,Post=Post))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form,Post=Post)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username,Post=Post))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user,Post=Post)

@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    no_notice = 0
    return render_template('post.html', posts=[post], form=form,Post = Post,
                           no_notice = no_notice,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id,Post = Post))
    form.body.data = post.body
    return render_template('edit_post.html', form=form,Post=Post,)


@main.route('/follow/<username>')
@login_required
#@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
#@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

@main.route('/tagcloud', methods=['GET', 'POST'])
def tagcloud():
    Cloud=TagCloud(4,6)
    #size = TagCluod.get_tag_font_size()
    #flash('tagcloud')
    return render_template('tagcloud.html',Cloud=Cloud,Tag=Tag)

@main.route('/Category',methods=['GET','POST'])
def Category():
    posts = Post.query.filter_by(category_id=2).all()
    #return redirect(url_for('.Category'))
    return render_template('Category.html',posts = posts)

@main.route('/Edit',methods=['GET','POST'])
def Edit():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(post_notice = form.post_notice.data,
                    body=form.body.data,
                    b_title=form.b_title.data,
                    category_id=form.category_id.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        nametest=form.name.data
        counts=nametest.count
        for taglist in nametest.split(';') :
            #for u in post.tags.order_by(Tag.id).all():
                if taglist :#and (u is None or u!=taglist):
                    tag = Tag.query.filter_by(name=taglist).first()
                    if not tag :
                        tag = Tag(name=taglist,
                                count=1
                                )
                    else:

                        tag.count=tag.count+1
                    db.session.add(tag)
                    post.tags.append(tag)
                    db.session.add(post)
                        #post_tags=post.tags.order_by(Tag.id).all()


                #if i>=5 :
        #if post.tags.order_by(Tag.id).all() is not None:
        #session['tagsname'] = post.tags.order_by(Tag.id).all()
        #for u in post.tags.order_by(Tag.id).all():

        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items


    return render_template('Edit.html', form=form, posts=posts,

                           pagination=pagination,
                           tagsname=session.get('tagsname'))

@main.route('/Category_name/<name>',methods=['GET','POST'])
def Category_name(name):
    #posts = Post.query.filter_by(categorys = name).all()
    category = Category.query.filter_by(name=name).first_or_404()
    posts = category.posts.order_by(Post.timestamp.desc()).all()
    #return redirect(url_for('.Category'))
    C_titel = name
    return render_template('Category.html',posts = posts,C_titel = C_titel,Post = Post)


@main.route('/PYTHON',methods=['GET','POST'])
def PYTHON():
    posts = Post.query.filter_by(category_id = 1).all()
    #return redirect(url_for('.Category'))
    C_titel = 'PYTHON'
    return render_template('Category.html',posts = posts,C_titel = C_titel,Post = Post)

@main.route('/Database',methods=['GET','POST'])
def Database():
    posts = Post.query.filter_by(category_id = 2).all()
    #return redirect(url_for('.Category'))
    C_titel = 'Database'
    return render_template('Category.html',posts = posts,C_titel = C_titel,Post = Post)

@main.route('/html\/css',methods=['GET','POST'])
def html():
    posts = Post.query.filter_by(category_id = 3).all()
    #return redirect(url_for('.Category'))
    C_titel = 'html/css'
    return render_template('Category.html',posts = posts,C_titel = C_titel,Post = Post)

@main.route('/others',methods=['GET','POST'])
def others():
    posts = Post.query.filter_by(category_id = 4).all()
    #return redirect(url_for('.Category'))
    C_titel = 'others'
    return render_template('Category.html',posts = posts,C_titel = C_titel,Post = Post)