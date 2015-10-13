from flask import url_for
from flask.ext.login import LoginManager, login_required, logout_user
login_manager = LoginManager()
from .sqlalchemy_models import User, Role
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from alguito.datastore import db


def init_login_manager(app):
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security = Security(app, user_datastore)
    # Not sure we need this step, YAGNI?
    app.security = security


@login_manager.user_loader
def load_user_by_id(id):
    try:
        return User.get(id)
    except:
        return None