# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import random

import bcrypt

from mediagoblin.tools.mail import send_email
from mediagoblin.tools.template import render_template
from mediagoblin import mg_globals


def bcrypt_check_password(raw_pass, stored_hash, extra_salt=None):
    """
    Check to see if this password matches.

    Args:
    - raw_pass: user submitted password to check for authenticity.
    - stored_hash: The hash of the raw password (and possibly extra
      salt) to check against
    - extra_salt: (optional) If this password is with stored with a
      non-database extra salt (probably in the config file) for extra
      security, factor this into the check.

    Returns:
      True or False depending on success.
    """
    if extra_salt:
        raw_pass = u"%s:%s" % (extra_salt, raw_pass)

    hashed_pass = bcrypt.hashpw(raw_pass.encode('utf-8'), stored_hash)

    # Reduce risk of timing attacks by hashing again with a random
    # number (thx to zooko on this advice, which I hopefully
    # incorporated right.)
    #
    # See also:
    rand_salt = bcrypt.gensalt(5)
    randplus_stored_hash = bcrypt.hashpw(stored_hash, rand_salt)
    randplus_hashed_pass = bcrypt.hashpw(hashed_pass, rand_salt)

    return randplus_stored_hash == randplus_hashed_pass


def bcrypt_gen_password_hash(raw_pass, extra_salt=None):
    """
    Generate a salt for this new password.

    Args:
    - raw_pass: user submitted password
    - extra_salt: (optional) If this password is with stored with a
      non-database extra salt
    """
    if extra_salt:
        raw_pass = u"%s:%s" % (extra_salt, raw_pass)

    return unicode(
        bcrypt.hashpw(raw_pass.encode('utf-8'), bcrypt.gensalt()))


def fake_login_attempt():
    """
    Pretend we're trying to login.

    Nothing actually happens here, we're just trying to take up some
    time, approximately the same amount of time as
    bcrypt_check_password, so as to avoid figuring out what users are
    on the system by intentionally faking logins a bunch of times.
    """
    rand_salt = bcrypt.gensalt(5)

    hashed_pass = bcrypt.hashpw(str(random.random()), rand_salt)

    randplus_stored_hash = bcrypt.hashpw(str(random.random()), rand_salt)
    randplus_hashed_pass = bcrypt.hashpw(hashed_pass, rand_salt)

    randplus_stored_hash == randplus_hashed_pass


EMAIL_VERIFICATION_TEMPLATE = (
    u"http://{host}{uri}?"
    u"userid={userid}&token={verification_key}")


def send_verification_email(user, request):
    """
    Send the verification email to users to activate their accounts.

    Args:
    - user: a user object
    - request: the request
    """
    rendered_email = render_template(
        request, 'mediagoblin/auth/verification_email.txt',
        {'username': user.username,
         'verification_url': EMAIL_VERIFICATION_TEMPLATE.format(
                host=request.host,
                uri=request.urlgen('mediagoblin.auth.verify_email'),
                userid=unicode(user.id),
                verification_key=user.verification_key)})

    # TODO: There is no error handling in place
    send_email(
        mg_globals.app_config['email_sender_address'],
        [user.email],
        # TODO
        # Due to the distributed nature of GNU MediaGoblin, we should
        # find a way to send some additional information about the
        # specific GNU MediaGoblin instance in the subject line. For
        # example "GNU MediaGoblin @ Wandborg - [...]".
        'GNU MediaGoblin - Verify your email!',
        rendered_email)


EMAIL_FP_VERIFICATION_TEMPLATE = (
    u"http://{host}{uri}?"
    u"userid={userid}&token={fp_verification_key}")


def send_fp_verification_email(user, request):
    """
    Send the verification email to users to change their password.

    Args:
    - user: a user object
    - request: the request
    """
    rendered_email = render_template(
        request, 'mediagoblin/auth/fp_verification_email.txt',
        {'username': user.username,
         'verification_url': EMAIL_FP_VERIFICATION_TEMPLATE.format(
                host=request.host,
                uri=request.urlgen('mediagoblin.auth.verify_forgot_password'),
                userid=unicode(user.id),
                fp_verification_key=user.fp_verification_key)})

    # TODO: There is no error handling in place
    send_email(
        mg_globals.app_config['email_sender_address'],
        [user.email],
        'GNU MediaGoblin - Change forgotten password!',
        rendered_email)
