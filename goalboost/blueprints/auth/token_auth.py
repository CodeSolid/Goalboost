from flask.ext.httpauth import HTTPBasicAuth
from flask import current_app
from goalboost.model.auth_models import User
from flask.ext.login import  login_user

httpBasicAuth = HTTPBasicAuth()


@httpBasicAuth.verify_password
def verify_password(username, password):
    if username is None or username == '':
        current_app.logger.error("Username null in verify_password; check value of WSGIPassAuthorization in apache config")
    user = User.verify_auth_token(password)
    if not user:
        return False
    # The next two lines set the current user correctly for the token case, on a
    # per-request basis,  Tthe user still needs to re-authenticate with each
    # request, so the RESTful statelessness is implemented correctly.
    user.authenticated = True
    login_user(user, remember=True)
    return True