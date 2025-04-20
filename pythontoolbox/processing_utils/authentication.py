from oauthlib.oauth2 import (
        InvalidGrantError, 
        LegacyApplicationClient, 
        OAuth2Token, 
        UnauthorizedClientError)
from requests_oauthlib import OAuth2Session
import requests

AUTH_TOKEN_URL = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/token"
AUTH_CLIENT_ID = "iq-web-client"
USER_INFO_URL = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/userinfo"


def get_access_token(username: str, 
                    password: str,
                    auth_token_url = AUTH_TOKEN_URL,
                    auth_client_id = AUTH_CLIENT_ID
                    ):
    """
    Get OAuth token from auth_token_url and store in config_path_tokenfile

    Input Args: 
        username (str): the entered username by the user
        password (str): the entered password by the user
        auth_token_url (str): the URL to which to send the http request
        auth_client_id (str): the client ID for authentication.
    
    Returns: 
        OAuth2Token or None: Token in JSON format with session information or None if any error
        str: either error message or success message
    """
    try:
        client = LegacyApplicationClient(client_id=auth_client_id)
        with OAuth2Session(client=client) as oauth_session:
            token = oauth_session.fetch_token(
                token_url=auth_token_url,
                client_id=auth_client_id,
                username=username,
                password=password
            )

            msg = "Successfully logged in."
            return token, msg
        
    except UnauthorizedClientError as e:
        err_msg = f"Authorisation failed for token url {auth_token_url} as client {auth_client_id}.\n{str(e)}"
    except InvalidGrantError as e:
        err_msg = f"Login failed.\nReason: {str(e)}"
    except Exception as e:
        err_msg = f"Unknown error on authentication for token url {auth_token_url} as client {auth_client_id}.\n{str(e)}"
    return None, err_msg

   
def refresh_token(token: OAuth2Token, 
                  auth_token_url=AUTH_TOKEN_URL, 
                  auth_client_id=AUTH_CLIENT_ID
                  ):
    """
    Refresh OAuth token using auth_token_url.

    Input Args:
        token (OAuth2Token): The current OAuth2 token that needs to be refreshed.
        auth_token_url (str): The URL to request a new token.
        auth_client_id (str): The client ID for authentication.
    
    Returns:
        OAuth2Token or None: The refreshed token in JSON format or None if an error occurs.
        str: Either an error message or a success message.
    """
    try:
        client = LegacyApplicationClient(client_id=auth_client_id)
        with OAuth2Session(client=client, token=token) as oauth_session:
            new_token = oauth_session.refresh_token(
                token_url=auth_token_url, 
                client_id=auth_client_id
            )
            
            msg = "Token successfully refreshed."
            return new_token, msg

    except UnauthorizedClientError as e:
        err_msg = f"Authorization failed for token URL {auth_token_url} as client {auth_client_id}.\n{str(e)}"
    except InvalidGrantError as e:
        err_msg = f"Token refresh failed.\nReason: {str(e)}"
    except Exception as e:
        err_msg = f"Unknown error while refreshing token for URL {auth_token_url} as client {auth_client_id}.\n{str(e)}"

    return None, err_msg


def get_preferred_username(access_token: str):
    
    headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}

    with requests.Session() as s:
        s.headers.update(headers)
        user_info = s.get(USER_INFO_URL).json()

    return user_info