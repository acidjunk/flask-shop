import datetime
import uuid

import os
from flask import Flask, flash, request, url_for
from flask_admin import helpers as admin_helpers
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_login import UserMixin, current_user
from flask_mail import Mail
from flask_migrate import Migrate, MigrateCommand
from flask_restplus import Api, Resource, fields, marshal_with
from flask_script import Manager
from flask_security import RoleMixin, SQLAlchemyUserDatastore, Security, utils
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from sqlalchemy.dialects.postgresql.base import UUID
from wtforms import PasswordField

VERSION = '0.1.0'
DATABASE_URI = os.getenv('DATABASE_URI', 'postgres://flask-shop:flask-shop@localhost/flask-shop')

app = Flask(__name__, static_url_path='/static')
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
    email = db.Column(db.String(255), unique=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
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
    name = db.Column(db.String(255), index=True)
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
    name = db.Column(db.String(255), unique=True, index=True)

    def __repr__(self):
        return self.name


class CategoryToProduct(db.Model):
    __tablename__ = 'categories_to_products'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    category_id = db.Column('category_id', db.UUID(as_uuid=True), db.ForeignKey('categories.id'))
    product_id = db.Column('product_id', db.UUID(as_uuid=True), db.ForeignKey('products.id'))


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(255), unique=True, index=True)
    list_image = db.Column(db.String(255), index=True)
    detail_image = db.Column(db.String(255), index=True)
    content = db.Column(db.Text)
    price = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    categories = db.relationship('Category', secondary='categories_to_products',
                                 backref=db.backref('products', lazy='dynamic'))

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
    column_hide_backrefs = False
    column_list = ('email', 'active', 'roles')


class RolesAdminView(ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        #todo only admins and operators allowed
        return current_user.is_authenticated


class ProductAdminView(ModelView):
    column_list = ['id', 'name', 'is_active', 'created_on']
    column_default_sort = ('name', True)
    column_filters = ('is_active', )
    column_searchable_list = ('name', )

    def is_accessible(self):
        #todo only admin, moderators and operators allowed
        return current_user.is_authenticated


class CategoryAdminView(ModelView):
    column_list = ['id', 'name']
    column_default_sort = ('name', True)
    column_searchable_list = ('name', )

    def is_accessible(self):
        #todo only admin, moderators and operators allowed
        return current_user.is_authenticated


class CustomerAdminView(ModelView):
    column_list = ['id', 'name']
    column_default_sort = ('name', True)
    column_searchable_list = ('name', )

    def is_accessible(self):
        #todo only admin, moderators and operators allowed
        return current_user.is_authenticated


class ShoppingCartAdminView(ModelView):
    column_list = ['id']

    def is_accessible(self):
        #todo only admin, moderators and operators allowed
        return current_user.is_authenticated


admin.add_view(ProductAdminView(Product, db.session))
admin.add_view(CategoryAdminView(Category, db.session))
admin.add_view(CustomerAdminView(Customer, db.session))
admin.add_view(ShoppingCartAdminView(ShoppingCart, db.session))
admin.add_view(UserAdminView(User, db.session))
admin.add_view(RolesAdminView(Role, db.session))


@api.route('/api/products')
class ProductListResource(Resource):

    @marshal_with({'id': fields.String, 'name': fields.String, 'list_image': fields.String,
                   'detail_image': fields.String, 'content': fields.String, 'price': fields.Float})
    def get(self):
        args = request.args
        if args:
            products = Product.query.filter(Product.name.contains(args["search_phrase"])).all()
        else:
            products = Product.query.all()
        return products


if __name__ == '__main__':
    manager.run()
