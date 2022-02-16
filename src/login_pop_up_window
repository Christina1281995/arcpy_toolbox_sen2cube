import arcpy
import requests_oauthlib
import oauthlib
import json
import os
import getpass

import tkinter as tk
import tkinter.ttk as ttk

from datetime import datetime
from oauthlib.oauth2 import InvalidGrantError, LegacyApplicationClient, OAuth2Token, \
  UnauthorizedClientError
from requests import Response
from requests_oauthlib import OAuth2Session

# envs
auth_token_url = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/token"
auth_client_id = "iq-web-client"

def fetch_token(username: str, password: str,
                auth_token_url: str,
                auth_client_id: str,
                ) -> OAuth2Token:
  """
  Get OAuth token from auth_token_url and store in config_path_tokenfile
  :return: OAuth2Token with session information or None if any error
  """
  try:
    client: Final[LegacyApplicationClient] = LegacyApplicationClient(client_id=auth_client_id)
    with OAuth2Session(client=client) as oauth_session:
      token: Final[OAuth2Token] = oauth_session.fetch_token(
        token_url=auth_token_url,
        client_id=auth_client_id,
        username=username,
        password=password
      )
      arcpy.AddMessage(f"Login successful. Got token: {token}")
      return token

  except UnauthorizedClientError:
    arcpy.AddErrorMessage(
      f"Authorisation failed for token url {auth_token_url} as client {auth_client_id}.",
      exc_info=True,
    )
  except InvalidGrantError as e:
    arcpy.AddErrorMessage(f"Login failed. Reason {str(e)}", exc_info=False)
  except Exception:
    arcpy.AddErrorMessage(
      f"Unknown error on authentication for token url {auth_token_url} as client {auth_client_id}.",
      exc_info=True,
    )



# This is used to execute code if the file was run but not imported
if __name__ == '__main__':


    token = ""

    first = tk.Tk()
    s = ttk.Style()
    s.theme_use('alt')

    first.geometry('400x150')
    first.title('Sen2Cube Login Window')



    L1 = tk.Label(first, text="Username:", font=(14)).grid(row=0, column=0, padx=5, pady=5)
    L2 = tk.Label(first, text="Password:", font=(14)).grid(row=1, column=0, padx=5, pady=5)


    username_input = tk.StringVar()
    password_input = tk.StringVar()

    t1 = tk.Entry(first, textvariable=username_input, font=(14)).grid(row=0,column=1)
    t2 = tk.Entry(first, textvariable=password_input, font=(14), show='*').grid(row=1, column=1)

    def login():
      username = username_input.get()
      password = password_input.get()
      arcpy.AddMessage('Attempting login .... ')
      arcpy.AddMessage("Username = " + username + "\nPassword = " + password)
      result = fetch_token(username, password, auth_token_url, auth_client_id)
      print(result)
      token = result
      return token


    def cancel():
      arcpy.AddMessage('was cancelled')

    b1 = tk.Button(first, command=login, text='Login', font=(14)).grid(row=2, column=1, sticky=tk.W)
    b2 = tk.Button(first, command=cancel, text='Cancel', font=(14)).grid(row=2, column=1, sticky=tk.E)

    first.mainloop()


