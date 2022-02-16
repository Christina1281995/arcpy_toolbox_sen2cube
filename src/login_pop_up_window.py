"""
Tool:               Sen2Cube ArcGIS PoC
Source Name:        <File name>
Version:            ArcGIS Pro 2.9
Author:             Niklas Jaggy, Christina Zorenboehmer
Usage:              <Command syntax>
Required Arguments: <parameter0>
                    <parameter1>
Optional Arguments: <parameter2>
                    <parameter3>

Description:        This script tool serves as a simple proof of concept. It demonstrates the compatibility
                    of the Sen2Cube EO Data Cube with ArcGIS Pro such that registered users can access the
                    application directly from within their ArcGIS Pro desktop software.
"""
import arcpy
import requests_oauthlib
import oauthlib
import json
import os

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

    # create pop-up window for log in as soon as "Run" is clicked
    popup = tk.Tk()
    #style elements
    s = ttk.Style()
    s.theme_use('alt')
    popup.geometry('400x150')
    popup.title('Sen2Cube Login')
    # icon
    # TODO: figure out how to add online URL in here.
    popup.iconbitmap(r"C:\Users\b1080788\Documents\sen2icon.ico")

    # pop up window content
    L1 = tk.Label(popup, text="Username:", font=(14)).grid(row=0, column=0, padx=15, pady=15)
    L2 = tk.Label(popup, text="Password:", font=(14)).grid(row=1, column=0, padx=5, pady=5)

    username_input = tk.StringVar()
    password_input = tk.StringVar()

    # text entries (censor password entry)
    t1 = tk.Entry(popup, textvariable=username_input, font=(14)).grid(row=0, column=1)
    t2 = tk.Entry(popup, textvariable=password_input, font=(14), show='\u2022').grid(row=1, column=1)

    # button functions
    def login():
      username = username_input.get()
      password = password_input.get()
      arcpy.AddMessage('Attempting login .... ')
      arcpy.AddMessage("Username = " + username + "\nPassword = " + password)
      result = fetch_token(username, password, auth_token_url, auth_client_id)
      print(result)
      token = result
      popup.destroy()
      return token


    def cancel():
      arcpy.AddError('Login process was cancelled.')
      popup.destroy()
      sys.exit(0)


    popup.bind('<Return>', login)

    b1 = tk.Button(popup, command=login, text='Login', font=(14)).grid(row=2, column=1, sticky=tk.W)
    b2 = tk.Button(popup, command=cancel, text='Cancel', font=(14)).grid(row=2, column=1, sticky=tk.E)

    popup.mainloop()


