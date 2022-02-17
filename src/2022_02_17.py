"""
Tool:               Sen2Cube ArcGIS PoC

Source Name:        <File name>
Version:            ArcGIS Pro 2.9
Python Environment: Cloned default Python 3.7 Environment
                    Added Package: "Typing"

Authors:            Niklas Jaggy, Christina Zorenboehmer

Usage:              <Command syntax>

Required Arguments: <parameter0> Area of Interest
                    <parameter1> Factbase
                    <parameter2> Knowledgebase
                    <parameter3> Start Date
                    <parameter4> End Date
                    <parameter5> Output Directory

Optional Arguments: <parameter>
                    <parameter>

Description:        This script tool serves as a simple proof of concept. It demonstrates the compatibility
                    of the Sen2Cube EO Data Cube with ArcGIS Pro such that registered users can access the
                    application directly from within their ArcGIS Pro desktop software.
"""


# -------------------------------------------------- IMPORTS-----------------------------------------------------------
import arcpy
import requests
import requests_oauthlib
import oauthlib
import json
import os
import time
import urllib


import tkinter as tk
import tkinter.ttk as ttk

from datetime import datetime
from oauthlib.oauth2 import InvalidGrantError, LegacyApplicationClient, OAuth2Token, \
  UnauthorizedClientError
from requests import Response
from requests_oauthlib import OAuth2Session


# ---------------------------------------------- ENVS AND FUNCTIONS ----------------------------------------------------

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
      # arcpy.AddMessage(f"Login successful. Got token: {token}")
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

#-------------------------------------- STEP 1: USER LOGIN AND GET TOKEN ----------------------------------------------

    token_text = ""

    # create pop-up window for log in as soon as "Run" is clicked
    popup = tk.Tk()
    #style elements
    s = ttk.Style()
    s.theme_use('alt')
    popup.geometry('400x150')
    popup.title('Sen2Cube User Login')
    popup.eval('tk::PlaceWindow . center')

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
      arcpy.AddMessage('Attempting login ... ')
      global token_text
      token_text = fetch_token(username, password, auth_token_url, auth_client_id)
      arcpy.AddMessage('Login successful.\n')
      popup.destroy()

    def cancel():
      arcpy.AddError('Login process was cancelled.')
      popup.destroy()
      sys.exit(0)

    # TODO check and make sure the enter fucntionality works
    popup.bind('<Return>', login)

    b1 = tk.Button(popup, command=login, text='Login', font=(14)).grid(row=2, column=1, sticky=tk.W)
    b2 = tk.Button(popup, command=cancel, text='Cancel', font=(14)).grid(row=2, column=1, sticky=tk.E)

    popup.mainloop()


# ------------------------------------- STEP 2: SEND POST INFERENCE REQUEST -------------------------------------------

    # TODO make dynamic

    inference_body = {
        "data": {
            "type": "inference",
            "attributes": {
                "owner": "niklas.jaggy",
                "area_of_interest": "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[13.024892807006836,47.780058823502834],[13.072528839111328,47.780058823502834],[13.072528839111328,47.80958073682116],[13.024892807006836,47.80958073682116],[13.024892807006836,47.780058823502834]]]}}]}",
                "temp_range_start": "2018-01-01T00:00:00+00:00",
                "temp_range_end": "2018-12-31T23:59:59.999000+00:00",
                "comment": "snow_timeseries - dieser Kommentar kann dazu dienendie inference wiederzuerkennen. Hier könnt ihr auch eure eigenen IDsunterbringen etc.",
                "favourite": True,
                "output_scale_factor": 1
            },
            "relationships": {
                "knowledgebase": {
                    "data": {
                        "type": "knowledgebase",
                        "id": "2150"
                    }
                },
                "factbase": {
                    "data": {
                        "type": "factbase",
                        "id": "-"
                    }
                }
            }
        }
    }
    arcpy.AddMessage(inference_body)

    knowledgebase_id = "2150"

    # factbase handle user input and update inference body
    factbase_input = arcpy.GetParameterAsText(1)
    if factbase_input == "1 - Austria":
        factbase_id = "1"
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "1"
    elif factbase_input == "2 - Afghanistan":
        factbase_id = "2"
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "2"
    elif factbase_input == "3 - Syria":
        factbase_id = "3"
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "3"

   arcpy.AddMessage(inference_body)
    """
    inference_body = {
        "data": {
            "type": "inference",
            "attributes": {
                "owner": "niklas.jaggy",
                "area_of_interest": "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[13.024892807006836,47.780058823502834],[13.072528839111328,47.780058823502834],[13.072528839111328,47.80958073682116],[13.024892807006836,47.80958073682116],[13.024892807006836,47.780058823502834]]]}}]}",
                "temp_range_start": "2018-01-01T00:00:00+00:00",
                "temp_range_end": "2018-12-31T23:59:59.999000+00:00",
                "comment": "snow_timeseries - dieser Kommentar kann dazu dienendie inference wiederzuerkennen. Hier könnt ihr auch eure eigenen IDsunterbringen etc.",
                "favourite": True,
                "output_scale_factor": 1
            },
            "relationships": {
                "knowledgebase": {
                    "data": {
                        "type": "knowledgebase",
                        "id": "2150"
                    }
                },
                "factbase": {
                    "data": {
                        "type": "factbase",
                        "id": "1"
                    }
                }
            }
        }
    }
    """

    # Assemble Post Request
    headers = {'Authorization':'Bearer {}'.format(token_text["access_token"]), 'Content-Type':'application/json'}
    url = "https://api.sen2cube.at/v1/inference"
    data = json.dumps(inference_body)
    arcpy.AddMessage('Creating the inference request...')

    # Send Post Request
    with requests.Session() as s:
        s.headers.update(headers)
        inf_post = s.post(url=url, data=data).json()
        # Get Inference ID
        inference_id = inf_post.get("data", {}).get("id")
    s.close()

    # Inform user - print inference ID
    arcpy.AddMessage("The inference ID for this request is: " + str(inference_id))


# --------------------------- STEP 3: SEND GET REQUEST WITH INFERENCE ID TO CHECK STATUS -------------------------------

    inference_endpoint = "https://api.sen2cube.at/v1/inference/" + str(inference_id)

    global status
    status = "-"

    while status != "SUCCEEDED":
        # send request
        with requests.Session() as s:
            s.headers.update(headers)
            inference_current = s.get(inference_endpoint).json()
            # update status
            status = str(inference_current["data"]["attributes"]["status"])
            # inform user
            arcpy.AddMessage('Your inference (ID: ' + str(inference_id) + ') is being processed. Current status: ' + status)
        # wait a little
        time.sleep(10)

    arcpy.AddMessage('Inference ' + str(inference_id) + ' is complete.')
    with requests.Session() as s:
        s.headers.update(headers)
        inference_complete = s.get(inference_endpoint).json()
        arcpy.AddMessage(inference_complete)






# --------------------------- STEP 4: ASK USER FOR FOLDER LOCATOIN AND DOWNLOAD GEOTIFF -------------------------------

"""
    # get user input
    out_dir = arcpy.GetParameter(3)
    arcpy.AddMessage(out_dir)

    # Download files
    # Parse filename
    fname = "made-up.TIF"  # TODO properly
    outfp = os.path.join(outdir, fname)
    # Download the file if it does not exist already
    if not os.path.exists(outfp):
        print("Downloading", fname)
        r = urllib.request.urlretrieve(url, outfp)

"""
