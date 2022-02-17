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

# TODO: Try to avoid having to clone python environment and install "Typing"

# -------------------------------------------------- IMPORTS-----------------------------------------------------------
import sys

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
    username = ""

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


    # Enter Key Function
    def enter(event):
        global username
        username = username_input.get()
        password = password_input.get()
        arcpy.AddMessage('Attempting login... ')
        global token_text
        token_text = fetch_token(username, password, auth_token_url, auth_client_id)
        arcpy.AddMessage('Login successful.')
        popup.destroy()

    popup.bind('<Return>', enter)

    # Login Button Function
    def login():
      global username
      username = username_input.get()
      password = password_input.get()
      arcpy.AddMessage('Attempting login... ')
      global token_text
      token_text = fetch_token(username, password, auth_token_url, auth_client_id)
      arcpy.AddMessage('Login successful.')
      popup.destroy()

    # Cancel Button Function
    def cancel():
      arcpy.AddError('Login process was cancelled.')
      popup.destroy()
      sys.exit(0)

    b1 = tk.Button(popup, command=login, text='Login', font=(14)).grid(row=2, column=1, sticky=tk.W)
    b2 = tk.Button(popup, command=cancel, text='Cancel', font=(14)).grid(row=2, column=1, sticky=tk.E)

    popup.mainloop()


# ------------------------------------- STEP 2: SEND POST INFERENCE REQUEST -------------------------------------------


    # to add dynamically: owner, AOI, temp_range_start, temp_range_end, comment, knowledgebase id, factbase id
    inference_body = {
        "data": {
            "type": "inference",
            "attributes": {
                "owner": "-",
                "area_of_interest": "-",
                "temp_range_start": "-",
                "temp_range_end": "-",
                "comment": "-",
                "favourite": True,
                "output_scale_factor": 1
            },
            "relationships": {
                "knowledgebase": {
                    "data": {
                        "type": "knowledgebase",
                        "id": "-"
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


    # TODO get Area of Interest Dynamically
    # TODO: implement checks on AOI (area size, location within given Factbase)
    # TODO: arcpy function to get information on CRS, then get extent in that CRS and use for AOI

    """

    # Insert Area of Interest into Inference Body Text
    aoi_input = arcpy.GetParameter(0)
    #arcpy.AddMessage(arcpy.desc(aoi_input))
    desc = arcpy.Describe(aoi_input)
    if desc.shapeType == "Polygon":
        extent = desc.Extent
        # arcpy.AddMessage(extent)

    # new = arcpy.management.CalculateGeometryAttributes(aoi_input, ["EXTENT_MIN_X", "EXTENT_MIN_Y", "EXTENT_MAX_X", "EXTENT_MAX_Y"], "DD")
    # arcpy.AddMessage(new)
    
    # outJson = ""
    """

    #outJson = arcpy.conversion.FeaturesToJSON(aoi_input, "outJson.json")
    #aoiString = json.dumps(outJson)
    #arcpy.AddMessage(outJson)

    lower_left = ""
    lower_right = ""
    upper_left = ""
    upper_right = ""

    #1447891,6342 6066794,4199 1458410,0056 6078143,4321
    # BBOX coordinate order: lower-left, lower-right, upper-right, upper-left
    aoi = "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[13.024892807006836,47.780058823502834],[13.072528839111328,47.780058823502834],[13.072528839111328,47.80958073682116],[13.024892807006836,47.80958073682116],[13.024892807006836,47.780058823502834]]]}}]}"
    # aoi = "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[" + str(lower_left) + "],[" + str(lower_right) + "],[" + str(upper_right) + "],[" + str(upper_left) + "],[" + str(lower_left) + "]]]}}]}"

    inference_body["data"]["attributes"]["area_of_interest"] = aoi

    # Insert username into inference body text
    inference_body["data"]["attributes"]["owner"] = str(username)

    # TODO: Implement checks on time
    # Insert Temp Ranges into Inference Body Text
    start = arcpy.GetParameter(3)
    end = arcpy.GetParameter(4)

    # Check validity of entry
    if end < start:
        arcpy.AddError("The selected End Date is before the selected Start Date")
        sys.exit(0)

    trs = start.strftime("%Y-%m-%dT00:00:00.000Z")
    tre = end.strftime("%Y-%m-%dT23:59:59.999Z")

    inference_body["data"]["attributes"]["temp_range_start"] = str(trs)
    inference_body["data"]["attributes"]["temp_range_end"] = str(tre)

    # Insert Knowledgebase into Inference Body Text
    knowledgebase_input = arcpy.GetParameterAsText(2)
    if knowledgebase_input == "00a - Hello World I":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2150"
    elif knowledgebase_input == "01 - Count Water Presence":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2158"
    elif knowledgebase_input == "02 - Vegetation vs Baresoil (Agricultural activity)":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2154"
    elif knowledgebase_input == "03 - Urban Green Areas":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2159"
    elif knowledgebase_input == "04 - Cloud-Free Composite":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2155"
    elif knowledgebase_input == "05 - SCBIR - Cloud free":
        inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = "2153"

    # Insert Factbase into Inference Body Text
    factbase_input = arcpy.GetParameterAsText(1)
    if factbase_input == "1 - Austria":
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "1"
    elif factbase_input == "2 - Afghanistan":
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "2"
    elif factbase_input == "3 - Syria":
        inference_body["data"]["relationships"]["factbase"]["data"]["id"] = "3"

    # Insert Comment into Inference Body Text

    comment_input = arcpy.GetParameterAsText(5)
    if comment_input != "":
        inference_body["data"]["attributes"]["comment"] = str(comment_input)

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
    arcpy.AddMessage(f"The inference ID for this request is: {str(inference_id)}")



# --------------------------- STEP 3: SEND GET REQUEST WITH INFERENCE ID TO CHECK STATUS -------------------------------


    inference_endpoint = f"https://api.sen2cube.at/v1#/inference/{str(inference_id)}"

    global status
    status = "-"

    while status != "SUCCEEDED":
        # send request
        with requests.Session() as s:
            s.headers.update(headers)
            inference_current = s.get(inference_endpoint).json()
            # update status
            status = str(inference_current["data"]["attributes"]["status"])
            arcpy.AddMessage(
                f'Your inference (ID: {str(inference_id)}) is being processed. Current status: {status}')
            if status == "FAILED":
                arcpy.AddError("Inference failed")
                sys.exit(0)
            # inform user

        # wait a little
        time.sleep(10)

    global inference_complete

    arcpy.AddMessage(f'Inference {str(inference_id)} is complete.')

    with requests.Session() as s:
        s.headers.update(headers)
        inference_complete = s.get(inference_endpoint).json()

    # TODO: Check how many outputs there are and handle

    # Store some useful variables
    inference_output = json.loads(inference_complete["data"]["attributes"]["output"])
    output_url = inference_output[0]["data"]
    output_name = inference_output[0]["name"]
    output_type = inference_output[0]["file_type"]


# ---------------------------------- STEP 4: DOWNLOAD AND ADD INFERENCE TO MAP -----------------------------------------


    # User endpoint and data from inference to create download link
    download_link = f"https://demo.sen2cube.at{str(output_url)}"

    with requests.Session() as s:
        s.headers.update(headers)
        outfile = s.get(download_link)

        # Directory
        out_dir = arcpy.GetParameterAsText(6)
        # File name
        fname = f"{str(output_name)}.tiff"
        # Complete path
        local_file = os.path.join(str(out_dir), fname)
        # Current Python Project
        aprx = arcpy.mp.ArcGISProject('CURRENT')
        activeMap = aprx.activeMap

        # Check if file already exists
        if os.path.exists(local_file):
            arcpy.AddMessage(
                f"The file {str(fname)} already exists in the specified directory. The current file will be added as a new version.")
            # Create new versioned file name
            i = 1
            while True:
                fname_new = str(output_name) + "(" + str(i) + ").tiff"
                local_file_new = os.path.join(str(out_dir), fname_new)
                if os.path.exists(local_file_new):
                    i = i + 1
                else:
                    with open(local_file_new, 'wb') as f:
                        f.write(s.get(download_link, allow_redirects=True).content)
                    arcpy.AddMessage(
                        f"The output file has been downloaded and stored at {str(local_file_new)}")
                    # Adding Layer to Map
                    activeMap.addDataFromPath(local_file_new)
                    break
        else:
            local_file = os.path.join(str(out_dir), fname)
            with open(local_file, 'wb') as file:
                file.write(s.get(download_link, allow_redirects=True).content)
            arcpy.AddMessage(f"The output file has been downloaded and stored at {str(local_file)}")
            # Adding Layer to Map
            activeMap.addDataFromPath(local_file)

        # Save to Project Geodatabase
        """
        db_file = os.path.join(str(aprx.defaultGeodatabase), fname)
        open(db_file, 'wb').write(s.get(download_link, allow_redirects=True).content)
        arcpy.AddMessage("The output file has been downloaded and stored at " + str(db_file))
        """
    s.close()
