from json import loads, dumps
from flask import current_app
from flask.ext.security import RoleMixin, UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
from mongoengine import signals
from goalboost.model import db
from goalboost.model.model_formatter import ModelFormatter

class Account(db.Document):
    name = db.StringField(max_length=255, unique=True)


    def get_users(self):
        return [user for user in User.objects(account=self.id)]

# User and Role use flask security mixins and are used by flask security
class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

    NONE = -1
    ROOT = 1;
    ACCOUNT_ADMIN = 2;
    ACCONT_USER = 3;


# TODO Add a UserName, which should be unique for itself + Account
class User(db.Document, UserMixin):

    email = db.EmailField(max_length=255, unique=True, required=True)
    password = db.StringField(max_length=255)
    account= db.ReferenceField(Account, required=True)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])

    def get_role(self):
        roles = [role.name for role in self.roles]
        if "Root" in roles:
            role = Role.ROOT
        elif "Account Admin" in roles:
            role = Role.ACCOUNT_ADMIN
        elif "Account User" in roles:
            role = Role.ACCONT_USER
        else:
            role = Role.NONE
        return role

    @property
    def root(self): return self.get_role() == Role.ROOT

    @property
    def account_admin(self): return self.get_role() == Role.ACCOUNT_ADMIN

    @property
    def account_user(self): return self.get_role() == Role.ACCOUNT_USER


    # Work in progress, cf.
    # http://blog.miguelgrinberg.com/post/restful-authentication-with-flask
    # See also blueprints.auth.__init__py verify_auth_token comments
    # TODO -- better / more client funcs based on this:
    # Note this returns BYTES -- you need to bytes.decode('utf-8') first if being used by web client
    # 24 hour expire
    def get_auth_token(self, expiration = 60*60*24*365):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        token = s.dumps({ 'id': str(self.id) })
        return token.decode()


    def __repr__(self):
        accountId = None
        confirmed_at = None
        if self.account is not None:
            accountId= self.account.__repr__()
        if self.confirmed_at is not None:
            confirmed_at = self.confirmed_at.__repr__()
        return ('User(id={}, emaitype(self.user)l="{}", password="{}", accountId={}, active={}, confirmed_at={}, roles={})'.format(
            self.id.__repr__(), self.email, self.password, accountId, confirmed_at, self.roles.__repr__(),
            None))

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            current_app.logger.warn("Inside verify_password returning false, signature expired")
            return None # valid token, but expired
        except BadSignature:
            current_app.logger.warn("Inside verify_password returning false, Bad Signature")
            return None # invalid token
        user = User.objects(id=data['id']).first() #.query.get(data['id'])
        return user

    def public_json(self):
        json = self.to_json()
        as_dict = loads(json)
        del(as_dict["password"])
        return dumps(as_dict)

# ModelFormatter only defines an interface, and even there
# the Python idiom is unclear
class UserModelFormatter(ModelFormatter):
    def model_to_dict(self, object_as_model):
        if object_as_model is None:
            return None
        user_dict = dict()
        user_string_properties = ["id", "email", "confirmed_at"] # Password omitted - do not display
        for prop in user_string_properties:
            self.add_string_property(prop, object_as_model, user_dict)
        self.add_property("active", object_as_model, user_dict)

        # Make into AccountModelFormatter.model_to_dict
        user_dict["account"] = AccountModelFormatter().model_to_dict(object_as_model.account)

        return user_dict
        # Needs more testing:  roles = db.ListField(db.ReferenceField(Role), default=[])

    def dict_to_model(self, object_as_dict):
        raise NotImplementedError("UserModelFormatter::dict_to_model not implemented")

class AccountModelFormatter(ModelFormatter):
    def model_to_dict(self, object_as_model):
        if object_as_model is None:
            return None
        account_dict = dict()
        account_string_properties = ["id", "name"]
        for prop in account_string_properties:
            self.add_string_property(prop, object_as_model, account_dict)
        return account_dict

    def dict_to_model(self, object_as_dict):
        raise NotImplementedError("UserModelFormatter::dict_to_model not implemented")
