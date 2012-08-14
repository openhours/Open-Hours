# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
#
# The Original Code is reddit.
#
# The Original Developer is the Initial Developer.  The Initial Developer of
# the Original Code is reddit Inc.
#
# All portions of the code written by reddit are Copyright (c) 2006-2012 reddit
# Inc. All Rights Reserved.
###############################################################################

from os import urandom
from base64 import urlsafe_b64encode

from pycassa.system_manager import ASCII_TYPE, DATE_TYPE, UTF8_TYPE

from r2.lib.db import tdb_cassandra


def generate_token(size):
    return urlsafe_b64encode(urandom(size)).rstrip("=")


class Token(tdb_cassandra.Thing):
    """A unique randomly-generated token used for authentication."""

    _extra_schema_creation_args = dict(
        key_validation_class=ASCII_TYPE,
        default_validation_class=UTF8_TYPE,
        column_validation_classes=dict(
            date=DATE_TYPE,
            used=ASCII_TYPE
        )
    )

    @classmethod
    def _new(cls, **kwargs):
        if "_id" not in kwargs:
            kwargs["_id"] = cls._generate_unique_token()

        token = cls(**kwargs)
        token._commit()
        return token

    @classmethod
    def _generate_unique_token(cls):
        for i in range(3):
            token = generate_token(cls.token_size)
            try:
                cls._byID(token)
            except tdb_cassandra.NotFound:
                return token
            else:
                continue
        raise ValueError

    @classmethod
    def get_token(cls, _id):
        try:
            return cls._byID(_id)
        except tdb_cassandra.NotFound:
            return None


class ConsumableToken(Token):
    _defaults = dict(used=False)
    _bool_props = ("used",)
    _warn_on_partial_ttl = False

    @classmethod
    def get_token(cls, _id):
        token = super(ConsumableToken, cls).get_token(_id)
        if token and not token.used:
            return token
        else:
            return None

    def consume(self):
        self.used = True
        self._commit()


class OAuth2Client(Token):
    """A client registered for OAuth2 access"""
    token_size = 10
    client_secret_size = 20
    _defaults = dict(name="",
                     description="",
                     about_url="",
                     icon_url="",
                     secret="",
                     redirect_uri="",
                    )
    _use_db = True
    _connection_pool = "main"

    @classmethod
    def _new(cls, **kwargs):
        if "secret" not in kwargs:
            kwargs["secret"] = generate_token(cls.client_secret_size)
        return super(OAuth2Client, cls)._new(**kwargs)


class OAuth2AuthorizationCode(ConsumableToken):
    """An OAuth2 authorization code for completing authorization flow"""
    token_size = 20
    _ttl = 10 * 60
    _defaults = dict(ConsumableToken._defaults.items() + [
                         ("client_id", ""),
                         ("redirect_uri", ""),
                         ("scope", ""),
                     ]
                )
    _int_props = ("user_id",)
    _use_db = True
    _connection_pool = "main"

    @classmethod
    def _new(cls, client_id, redirect_uri, user_id, scope):
        return super(OAuth2AuthorizationCode, cls)._new(
                client_id=client_id,
                redirect_uri=redirect_uri,
                user_id=user_id,
                scope=scope)

    @classmethod
    def use_token(cls, _id, client_id, redirect_uri):
        token = cls.get_token(_id)
        if token and (token.client_id == client_id and
                      token.redirect_uri == redirect_uri):
            token.consume()
            return token
        else:
            return None


class OAuth2AccessToken(Token):
    """An OAuth2 access token for accessing protected resources"""
    token_size = 20
    _ttl = 10 * 60
    _defaults = dict(scope="",
                     token_type="bearer",
                    )
    _int_props = ("user_id",)
    _use_db = True
    _connection_pool = "main"

    @classmethod
    def _new(cls, user_id, scope):
        return super(OAuth2AccessToken, cls)._new(
                user_id=user_id,
                scope=scope)


class EmailVerificationToken(ConsumableToken):
    _use_db = True
    _connection_pool = "main"
    _ttl = 60 * 60 * 12
    token_size = 20

    @classmethod
    def _new(cls, user):
        return super(EmailVerificationToken, cls)._new(user_id=user._fullname,
                                                       email=user.email)

    def valid_for_user(self, user):
        return self.email == user.email


class PasswordResetToken(ConsumableToken):
    _use_db = True
    _connection_pool = "main"
    _ttl = 60 * 60 * 12
    token_size = 20

    @classmethod
    def _new(cls, user):
        return super(PasswordResetToken, cls)._new(user_id=user._fullname,
                                                   email_address=user.email,
                                                   password=user.password)

    def valid_for_user(self, user):
        return (self.email_address == user.email and
                self.password == user.password)
