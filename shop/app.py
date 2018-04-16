import datetime
import uuid

import os
from flask import Flask, abort, request, url_for
from flask_admin import helpers as admin_helpers
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_cors import CORS
from flask_login import UserMixin, current_user
from flask_mail import Mail
from flask_migrate import Migrate, MigrateCommand
from flask_restplus import Api, Resource, fields, marshal_with
from flask_script import Manager
from flask_security import RoleMixin, SQLAlchemyUserDatastore, Security, utils, http_auth_required
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from slugify import slugify
from sqlalchemy.dialects.postgresql.base import UUID
from wtforms import PasswordField

VERSION = '0.1.0'
DATABASE_URI = os.getenv('DATABASE_URI', 'postgres://flask-shop:flask-shop@localhost/flask-shop')

app = Flask(__name__, static_url_path='/static')
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', 'TODO:MOVE_TO_BLUEPRINT')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
app.config['SECURITY_PASSWORD_SALT'] = 'SALTSALTSALT'

# Replace the next six lines with your own SMTP server settings
app.config['SECURITY_EMAIL_SENDER'] = os.getenv('SECURITY_EMAIL_SENDER', 'no-reply@example.com')
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER') if os.getenv('MAIL_SERVER') else 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME') if os.getenv('MAIL_USERNAME') else 'no-reply@example.com'
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD') if os.getenv('MAIL_PASSWORD') else 'somepassword'

# More Flask Security settings
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_REGISTER_URL'] = '/admin/create_account'
app.config['SECURITY_LOGIN_URL'] = '/admin/login'
app.config['SECURITY_POST_LOGIN_VIEW'] = '/admin'
app.config['SECURITY_LOGOUT_URL'] = '/admin/logout'
app.config['SECURITY_POST_LOGOUT_VIEW'] = '/admin'
app.config['SECURITY_RESET_URL'] = '/admin/reset'
app.config['SECURITY_CHANGE_URL'] = '/admin/change'
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ['email', 'username']

# setup DB
db = SQLAlchemy(app)
db.UUID = UUID

api = Api(app, doc='/api/ui')
manager = Manager(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)
admin = Admin(app, name='Shop admin', template_mode='bootstrap3')
mail = Mail(app)


@app.context_processor
def version():
    return dict(version=VERSION)


# Define models
class RoleToUser(db.Model):
    __tablename__ = 'roles_to_users'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = db.Column('user_id', db.UUID(as_uuid=True), db.ForeignKey('users.id'))
    role_id = db.Column('role_id', db.UUID(as_uuid=True), db.ForeignKey('roles.id'))


class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    # __str__ is required by Flask-Admin, so we can have human-readable values for the Role when editing a User.
    def __str__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='roles_to_users',
                            backref=db.backref('users', lazy='dynamic'))
    customers = db.relationship('Customer', backref='user', lazy=True)
    # Human-readable values for the User when editing user related stuff.
    def __str__(self):
        return f'{self.username} : {self.email}'

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.email)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = db.Column('user_id', db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    first_name = db.Column(db.String(255), nullable=False, index=True)
    last_name = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(15), index=True)
    company_name = db.Column(db.String(255), index=True)
    vat_number = db.Column(db.String(30), index=True)
    street = db.Column(db.String(30), nullable=False, index=True)
    zip_code = db.Column(db.String(7), nullable=False, index=True)
    city = db.Column(db.String(255), nullable=False, index=True)
    country = db.Column(db.String(255), nullable=False, index=True)
    shopping_carts = db.relationship('ShoppingCart', backref='customer', lazy=True)

    def __repr__(self):
        return self.name


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)

    def __repr__(self):
        return self.name


class CategoryToProduct(db.Model):
    __tablename__ = 'categories_to_products'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    category_id = db.Column('category_id', db.UUID(as_uuid=True), db.ForeignKey('categories.id'))
    product_id = db.Column('product_id', db.UUID(as_uuid=True), db.ForeignKey('products.id'))


class CategoryToArticle(db.Model):
    __tablename__ = 'categories_to_articles'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    category_id = db.Column('category_id', db.UUID(as_uuid=True), db.ForeignKey('categories.id'))
    articles_id = db.Column('article_id', db.UUID(as_uuid=True), db.ForeignKey('articles.id'))


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    seo_name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    intro = db.Column(db.Text, nullable=False)
    list_image = db.Column(db.String(255), nullable=False, index=True)
    detail_image = db.Column(db.String(255), nullable=False, index=True)
    usp1 = db.Column(db.String(255), nullable=False)
    usp2 = db.Column(db.String(255), nullable=False)
    usp3 = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    categories = db.relationship('Category', secondary='categories_to_products',
                                 backref=db.backref('products', lazy='dynamic'))

    def __repr__(self):
        return self.name

    @property
    def url(self):
        return slugify(self.seo_name)


class Article(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(255), unique=True, index=True)
    content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_main = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    categories = db.relationship('Category', secondary='categories_to_articles',
                                 backref=db.backref('articles', lazy='dynamic'))

    def __repr__(self):
        return self.name


class CartToProduct(db.Model):
    __tablename__ = 'carts_to_products'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cart_id = db.Column('cart_id', db.UUID(as_uuid=True), db.ForeignKey('shopping_carts.id'))
    product_id = db.Column('product_id', db.UUID(as_uuid=True), db.ForeignKey('products.id'))


class ShoppingCart(db.Model):
    __tablename__ = 'shopping_carts'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = db.Column('customer_id', db.UUID(as_uuid=True), db.ForeignKey('customers.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    is_complete = db.Column(db.Boolean, default=False)


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )


# Executes before the first request is processed.
@app.before_first_request
def before_first_request():
    user_datastore.find_or_create_role(name='admin', description='God mode!')
    user_datastore.find_or_create_role(name='customer', description='Can buy products')

    # Create a default user.
    # Todo find a better way, as this potentially provide me and others access to shops that fork me
    encrypted_password = utils.hash_password('acidjunk@gmail.com')
    if not user_datastore.get_user('acidjunk@gmail.com'):
        user_datastore.create_user(email='acidjunk@gmail.com', password=encrypted_password)
        db.session.commit()
        user_datastore.add_role_to_user('acidjunk@gmail.com', 'admin')
        db.session.commit()


class UserAdminView(ModelView):
    # Don't display the password on the list of Users
    column_list = ('email', 'username', 'confirmed_at', 'roles', 'active')
    # Don't include the standard password field when creating or editing a User (but see below)
    form_excluded_columns = ('password',)

    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):
        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdminView, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):
        # If the password field isn't blank...
        if len(model.password2):
            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.hash_password(model.password2)


class RolesAdminView(ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True


class ArticleAdminView(ModelView):
    column_list = ['name', 'is_main', 'created_on', 'is_active']
    column_default_sort = ('name', True)
    column_filters = ('is_active', 'categories')
    column_searchable_list = ('name', )

    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True


class ProductAdminView(ModelView):
    column_list = ['image', 'name', 'seo_name', 'intro', 'categories', 'price', 'created_on', 'is_active']
    column_default_sort = ('name', True)
    column_filters = ('is_active', 'categories')
    column_searchable_list = ('name', )

    def _list_thumbnail(view, context, model, name):
        return Markup('<img width="150" src="%s">' % url_for('static', filename=f'images/{model.list_image}'))

    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True

    column_formatters = {
        'image': _list_thumbnail
    }


class CategoryAdminView(ModelView):
    column_list = ['id', 'name']
    column_default_sort = ('name', True)
    column_searchable_list = ('name', )

    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True


class CustomerAdminView(ModelView):
    column_list = ['id', 'first_name', 'last_name', 'phone', 'company_name', 'city', 'country']
    column_default_sort = ('last_name', True)
    column_searchable_list = ('first_name', 'last_name')

    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True


class ShoppingCartAdminView(ModelView):
    column_list = ['id']

    def is_accessible(self):
        if 'admin' in current_user.roles:
            return True


admin.add_view(ProductAdminView(Product, db.session))
admin.add_view(ArticleAdminView(Article, db.session))
admin.add_view(CategoryAdminView(Category, db.session))
admin.add_view(CustomerAdminView(Customer, db.session))
admin.add_view(ShoppingCartAdminView(ShoppingCart, db.session))
admin.add_view(UserAdminView(User, db.session))
admin.add_view(RolesAdminView(Role, db.session))


# **********
# API Stuff
# **********
class StaticImageUrl(fields.Raw):
    def format(self, value):
        return url_for('static', filename=fr'images/{value}', _external=True)


@api.route('/api/products')
class ProductListResource(Resource):

    @marshal_with({'id': fields.String, 'url': fields.String, 'name': fields.String, 'seo_name': fields.String,
                   'list_image': StaticImageUrl, 'detail_image': StaticImageUrl, 'content': fields.String,
                   'price': fields.Float, 'intro': fields.String, 'usp1': fields.String, 'usp2': fields.String,
                   'usp3': fields.String, 'categories': fields.List(fields.String)})
    def get(self):
        args = request.args
        if args:
            products = Product.query.filter(Product.name.contains(args["search_phrase"])).all()
        else:
            products = Product.query.all()
        return products


@api.route('/api/categories')
class CategoryListResource(Resource):

    @marshal_with({'id': fields.String, 'name': fields.String})
    def get(self):
        categories = Category.query.all()
        return categories


@api.route('/api/articles')
class ArticleListResource(Resource):

    @marshal_with({'id': fields.String, 'name': fields.String, 'content': fields.String, 'is_main': fields.Boolean,
                   'categories': fields.List(fields.String)})
    def get(self):
        args = request.args
        if args:
            articles = Article.query.filter(Article.name.contains(args["search_phrase"])).all()
        else:
            articles = Article.query.all()
        return articles


@api.route('/api/customer/<string:email>')
class CustomerResource(Resource):

    @http_auth_required
    @marshal_with({'id': fields.String, 'first_name': fields.String, 'last_name': fields.String, 'phone': fields.String,
                   'company_name': fields.String, 'vat_number': fields.String, 'street': fields.String,
                   'zip_code': fields.String, 'city': fields.String, 'country': fields.String})
    def get(self, email):
        if email == current_user.email:
            customer = Customer.query.filter_by(user_id=current_user.id).first()
            return customer if customer else abort(400, 'No linked customer found.')
        abort(403, 'Not allowed to fetch this customer with your user.')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return 'You want path: %s' % path



if __name__ == '__main__':
    manager.run()
