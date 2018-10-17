"""
 JWT authentication 

 Functions to verify a third party (firebase) token. Fetches public key from
 key server and verifies token, and that user has access to fieldprime 

 Author: Tim Erwin <tim.erwin@csiro.au>
 Date: CSIRO 2018
"""
import logging
import requests
from flask import g
import python_jwt as jwt
from jwcrypto import jwk
from flask_httpauth import HTTPTokenAuth

from config import JWT_URI, JWT_AUDIENCE, JWT_ISSUER
from fp_common.fpsys import verifyUserIdent, verifyUserEmail, fpSetupG

logger = logging.getLogger('fieldprime.auth.jwt')
jwt_auth = HTTPTokenAuth('Bearer')

def get_public_key(keyid):
    """
    Fetch public keys from key server

    Parameters
    ----------
    keyid : str
        The id of the public key to fetch from the key server.
        Can be found in the header of token with attribute kid
        Server URI is configured in conf.jwt

    Returns
    -------
    jwk
        a json web key (jwcrypto.jwk) of requested key
    """

    pubkey = None

    try:
        response = requests.get(JWT_URI, timeout=2)
    except:
        pubkey = None

    keys = response.json()
    if keyid in keys:
        #jwk does not like unicode...
        pubkey = jwk.JWK.from_pem(str(keys[keyid]))


    return pubkey


@jwt_auth.verify_token
def verify_jwt_token(token):
    """
    Verify json web token (jwt)

    Parameters
    ----------
    token : str
        The token sent to server in the header of the request

    Returns
    -------
    bool
        user is allowed to access system
    """

    is_valid_user = False

    # Get public key id defined in token header and fetch corresponding key
    try:
        header,claims = jwt.process_jwt(token)
    except Exception as e:
        logger.debug("Not a valid token %s" % str(e))
        return False

    # Process issuer and audience first as no point verifying jwt if
    # these are invalid
    if 'aud' not in claims or JWT_AUDIENCE != claims['aud']:
        logger.debug("Invalid audience")
        return False

    if 'iss' not in claims and JWT_ISSUER != claims['iss']:
        logger.debug("Invalid issuer")
        return False

    # Get public key and validate jwt
    keyid = header[u'kid']
    pub_key = get_public_key(keyid)

    try:
        header,claims = jwt.verify_jwt(token,pub_key,allowed_algs=['RS256'], checks_optional=True)
    except Exception as e:
        logger.debug("Token validation failed: %s" % str(e))
        return False

    # Verify user is allowed access to fieldprime
    userid = claims['serenity/aafIdent']
    ident,domain = userid.split('@')
    # If CSIRO domain user verify on ident otherwise on email
    if domain == 'csiro.au':
        is_valid_user,user = verifyUserIdent(ident)
    else:
        is_valid_user,user = verifyUserEmail(userid)

    if is_valid_user:
        # Should not be needed if using jwt auth? 
        # create/set new fieldprime token
        # g.newToken = generate_auth_token(user)
        # TODO: set these directly
        fpSetupG(g, userIdent=user)

    return is_valid_user
