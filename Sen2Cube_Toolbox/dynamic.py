"""
Tool:               Sen2Cube ArcGIS Proof of Concept
Source Name:        <File name>
Version:            ArcGIS Pro 2.9
Python Environment: Python 3.7
Authors:            Niklas Jaggy, Christina Zorenboehmer
Usage:              <Command syntax>
Required Arguments: <parameter0> Username
                    <parameter1> Password
                    <parameter2> Login (Boolean)
                    <parameter3> Factbase
                    <parameter4> Knowledgebase
                    <parameter5> Area of Interest
                    <parameter6> Start Date
                    <parameter7> End Date
                    <parameter10> Output Directory
Optional Arguments: <parameter8> Comment
                    <parameter9> Favourite
Description:        This script tool serves as a simple proof of concept. It demonstrates the compatibility
                    of the Sen2Cube EO Data Cube with ArcGIS Pro such that registered users can access the
                    application directly from within their ArcGIS Pro desktop software.
"""
# -------------------------------------------------- IMPORTS-----------------------------------------------------------
import arcpy
import sys
import os
import json
import requests
import logging
from arcgis.geometry import Point, Polyline, Polygon, Geometry
from arcgis.gis import GIS
from arcgis.geocoding import geocode
from arcgis.geometry import lengths, areas_and_lengths, project
import pandas as pd
import requests_oauthlib
import oauthlib
import time
import urllib
from urllib.request import urlopen
import tkinter as tk
import tkinter.ttk as ttk
from PIL import Image, ImageTk
from io import BytesIO
from datetime import datetime
from oauthlib.oauth2 import InvalidGrantError, LegacyApplicationClient, OAuth2Token, \
    UnauthorizedClientError
from requests import Response
from requests_oauthlib import OAuth2Session

# ---------------------------------------------- ENVS AND FUNCTIONS ----------------------------------------------------
logger = logging.getLogger(__name__)
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
            exc_info=True, )


def refresh_token(token: OAuth2Token, auth_token_url: str, auth_client_id: str) -> OAuth2Token:
    try:
        client: Final[LegacyApplicationClient] = LegacyApplicationClient(client_id=auth_client_id)
        with OAuth2Session(client=client, token=token) as oauth_session:
            token: Final[OAuth2Token] = oauth_session.refresh_token(auth_token_url, client_id=auth_client_id)
            # arcpy.AddMessage(f"Got token: {token}")
            # arcpy.AddMessage(f"Token refresh successful.")
            return token
    except UnauthorizedClientError:
        arcpy.AddError(f"Authorisation failed for token url {auth_token_url} as client {auth_client_id}.",
                       exc_info=True, )
    except InvalidGrantError as e:
        arcpy.AddError(f"Login failed. Reason {str(e)}", exc_info=False)
    except Exception:
        arcpy.AddError(f"Unknown error on authentication for token url {auth_token_url} as client {auth_client_id}.",
                       exc_info=True, )


def get_points(aoi_in):
    """
    Takes the input extent in the provided spatial reference (most likely web mercator 3857 units: coordinates in meters)
    and breaks it apart to form individual points. Those points are turned into arcpy geometries and
    then reprojected into the required WGS84 projection system with decimal degrees.
    A new array of reprojected points is returned.
    """

    # Get current active map
    activeMap = arcpy.mp.ArcGISProject("CURRENT").activeMap

    # Get Spatial Reference of Map (determines how the extent will be formatted)
    map_spatial_reference = activeMap.spatialReference.PCSCode
    # arcpy.AddMessage(f"Active Map Spatial Reference:  {str(activeMap.spatialReference.PCSCode)}")

    # new empty arrays for points
    points = []
    points1 = []
    reproj_points = []

    # in standard web mercator # left, bottom, right, top, nan, nan, nan, nan
    # split input and replace comma with dot (otherwise float() will not work)
    individual_units = str(aoi_in).split()
    for i in range(4):
        points1.append(individual_units[i].replace(",", "."))

    # point_lowerleft
    points.append(arcpy.Point(float(points1[0]), float(points1[1])))
    # point_lowerright
    points.append(arcpy.Point(float(points1[2]), float(points1[1])))
    # point_upperright
    points.append(arcpy.Point(float(points1[2]), float(points1[3])))
    # point_upperleft
    points.append(arcpy.Point(float(points1[0]), float(points1[3])))

    # Specify current map spatial reference
    spatial_reference = arcpy.SpatialReference(map_spatial_reference)

    # Reproject points and add to array "reproj_points"
    for point in points:
        # Create point geometry with points and given spatial reference
        pnt_geometry = arcpy.PointGeometry(point, spatial_reference)
        # Reproject to get required Decimal Degree units
        projectedPointGeometry = pnt_geometry.projectAs(arcpy.SpatialReference(4326))
        reproj_points.append(projectedPointGeometry)
        # arcpy.AddMessage(" X:  {0}".format(projectedPointGeometry.firstPoint.X))
        # arcpy.AddMessage(" Y:  {0}".format(projectedPointGeometry.firstPoint.Y))

    # return array of reprojected points
    return reproj_points


# This is used to execute code if the file was run but not imported
if __name__ == '__main__':

    # -------------------------------------- STEP 1: USER LOGIN AND GET TOKEN ------------------------------------------

    username = arcpy.GetParameterAsText(0)
    password = arcpy.GetParameterAsText(1)
    arcpy.AddMessage(u"\u200B")

    successful_login = False

    token_text = fetch_token(username, password, auth_token_url, auth_client_id)
    login_time = time.time()
    successful_login = True
    arcpy.AddMessage('Login successful.')
    arcpy.AddMessage('_________________')
    arcpy.AddMessage(u"\u200B")


    # ------------------------------------- STEP 2: SEND POST INFERENCE REQUEST ----------------------------------------

    # Sen2Cube Endpoints to be used for Get Requests to dynamically insert data into Inference
    fb_list = 'https://api.sen2cube.at/v1/factbase'
    kb_list = 'https://api.sen2cube.at/v1/knowledgebase'

    # Inference Template
    # To be added dynamically: owner, AOI, temp_range_start, temp_range_end, comment, knowledgebase id, factbase id
    inference_body = {
        "data": {
            "type": "inference",
            "attributes": {
                "owner": "-",
                "area_of_interest": "-",
                "temp_range_start": "-",
                "temp_range_end": "-",
                "comment": "-",
                "favourite": False,
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

    # ------ USERNAME ----------

    # Insert username into Inference Template
    inference_body["data"]["attributes"]["owner"] = str(username)

    # ------ FACTBASE ----------

    # Get User Input for Factbase: Parameter is the title of the factbase
    factbase_input = arcpy.GetParameterAsText(3)

    # Get Request for Factbases
    headers = {'Authorization': 'Bearer {}'.format(token_text['access_token'])}
    with requests.Session() as s:
        s.headers.update(headers)
        factbase = s.get(fb_list).json()

        # Search for the correct Title - then take that factbase's ID for Inference Template
        length = len(factbase['data'])
        for k in range(length):
            if factbase['data'][k]['attributes']['title'] == factbase_input:
                # Set ID in the Inference Template
                inference_body["data"]["relationships"]["factbase"]["data"]["id"] = factbase['data'][k]['id']

    # ------ KNOWLEDGEBASE ----------

    # Get User Input for Knowledgebase: Parameter is the title of the knowledgebase
    knowledgebase_input = arcpy.GetParameterAsText(4)
    payload = {'page[size]': 0}
    # Get Request for Knowledgebases
    with requests.Session() as s:
        s.headers.update(headers)
        knowledgebase = s.get(kb_list, params=payload).json()

        # Search for the correct Title - then take that knowledgebase's ID for Inference Template
        length_kb = len(knowledgebase['data'])
        for i in range(length_kb):
            if knowledgebase['data'][i]['attributes']['title'] == knowledgebase_input:
                # Set ID in the Inference Template
                inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = knowledgebase['data'][i]['id']

    # ------ AREA OF INTEREST ----------

    # TODO: implement checks on AOI (area size, location within given Factbase)
    # Get User Input for AOI: Parameter is an extent
    # The get_points() function defined above handles extent projection and point conversion
    aoi_points = get_points(arcpy.GetParameter(5))

    # BBOX coordinate order: lower-left, lower-right, upper-right, upper-left, lower-left
    aoi = "{\"type\":\"FeatureCollection\",\"features\":[{\"type\":\"Feature\",\"properties\":{},\"geometry\":{\"type\":\"Polygon\",\"coordinates\":[[[" + \
          str(aoi_points[0].firstPoint.X) + "," + str(aoi_points[0].firstPoint.Y) + "],[" + str(
        aoi_points[1].firstPoint.X) + "," + str(aoi_points[1].firstPoint.Y) + "],[" + \
          str(aoi_points[2].firstPoint.X) + "," + str(aoi_points[2].firstPoint.Y) + "],[" + str(
        aoi_points[3].firstPoint.X) + "," + str(aoi_points[3].firstPoint.Y) + "],[" + \
          str(aoi_points[0].firstPoint.X) + "," + str(aoi_points[0].firstPoint.Y) + "]]]}}]}"

    # Insert aoi into the Inference Template
    inference_body["data"]["attributes"]["area_of_interest"] = aoi

    # ------ TIME RANGE ----------

    # TODO: Implement checks on time
    # Get User Input on Time Range
    start = arcpy.GetParameter(6)
    end = arcpy.GetParameter(7)

    # Check Start Date is before End Date
    if end < start:
        arcpy.AddError("The selected End Date is before the selected Start Date")
        sys.exit(0)

    # Convert to correct format
    trs = start.strftime("%Y-%m-%dT00:00:00.000Z")
    tre = end.strftime("%Y-%m-%dT23:59:59.999Z")

    # Insert Temp Ranges into Inference Template
    inference_body["data"]["attributes"]["temp_range_start"] = str(trs)
    inference_body["data"]["attributes"]["temp_range_end"] = str(tre)

    # ------ COMMENT ----------

    # Insert Comment into Inference Body Text
    comment_input = arcpy.GetParameterAsText(8)
    if comment_input != "":
        inference_body["data"]["attributes"]["comment"] = str(comment_input)

    # ------ SAVE AS FAVOURITE ----------

    # Insert Favourite Preference into Inference Body Text
    favourite = arcpy.GetParameter(9)
    if favourite == True:
        inference_body["data"]["attributes"]["favourite"] = True
        # Default is False

    # ------ SEND REQUEST ----------

    # Assemble Post Request
    headers = {'Authorization': 'Bearer {}'.format(token_text["access_token"]), 'Content-Type': 'application/json'}
    url = "https://api.sen2cube.at/v1/inference"
    data = json.dumps(inference_body)
    arcpy.AddMessage('Creating inference request...')

    # Send Post Request
    with requests.Session() as s:
        s.headers.update(headers)
        inf_post = s.post(url=url, data=data).json()
        # Get Inference ID
        inference_id = inf_post.get("data", {}).get("id")

    s.close()

    # --------------------------- STEP 3: SEND GET REQUEST WITH INFERENCE ID TO CHECK STATUS -------------------------------

    inference_endpoint = f"https://api.sen2cube.at/v1/inference/{str(inference_id)}"
    global status
    status = "-"
    global refresh_token_text
    refresh_token_text = ""

    # Inform user
    arcpy.AddMessage(f"Inference ID: {str(inference_id)}")
    arcpy.AddMessage(u"\u200B")
    arcpy.AddMessage("The request is now being processed by Sen2Cube. This process may take up to a few minutes.")
    arcpy.AddMessage(
        "Do not terminate the tool during this time, otherwise the inference will not be loaded into the map.")
    arcpy.AddMessage(u"\u200B")

    # Start recording time to see how long inference takes
    t0 = time.time()
    # refresh set to false
    refresh = False

    while status != "SUCCEEDED":

        # Check if it's time to refresh token
        current_time = time.time()
        elapsed_time = current_time - login_time
        if elapsed_time > 200:
            # refresh
            refresh_token_text = refresh_token(token_text, auth_token_url, auth_client_id)
            refresh = True
            # Re-set timer
            login_time = time.time()

        if refresh_token_text != "":
            token_text = refresh_token_text

        headers = {'Authorization': 'Bearer {}'.format(token_text["access_token"]), 'Content-Type': 'application/json'}

        # Keep sending request every 10 seconds
        with requests.Session() as s:
            s.headers.update(headers)
            inference_current = s.get(inference_endpoint).json()
            # Update status
            prev_status = status
            status = str(inference_current["data"]["attributes"]["status"])
            if prev_status == status:
                arcpy.AddMessage('')
            else:
                arcpy.AddMessage(f'\nCurrent status: {str(status)}')
            if status == "FAILED":
                # Inform user
                arcpy.AddError("Inference failed.")
                sys.exit(0)
        # wait 10 seconds if not done yet
        if status != "SUCCEEDED":
            time.sleep(10)

    global inference_complete

    # Calculate time that it took to process inference
    t1 = time.time()
    diff = t1 - t0
    total = round(diff, 2)

    # Inform user
    arcpy.AddMessage('_________________')
    arcpy.AddMessage(u"\u200B")
    arcpy.AddMessage(f'Inference {str(inference_id)}:')
    arcpy.AddMessage(f'Completed in {str(total)} seconds')

    # Get results
    with requests.Session() as s:
        s.headers.update(headers)
        inference_complete = s.get(inference_endpoint).json()

    # Store some useful variables
    inference_output = json.loads(inference_complete["data"]["attributes"]["output"])
    output_url = []
    output_name = []
    output_type = []

    # Get each of the outputs
    for output in inference_output:
        output_type.append(output["file_type"])
        if output["file_type"] == "geotiff":
            output_url.append(output["data"].replace("4326.tiff","3035.tiff"))
        else:
            output_url.append(output["data"])
        output_name.append(output["name"])


    # ---------------------------------- STEP 4: DOWNLOAD AND ADD INFERENCE TO MAP -------------------------------------

    # Inform user
    nr_of_outputs = len(output_name)
    arcpy.AddMessage(f"Number of outputs generated: {str(nr_of_outputs)}")
    arcpy.AddMessage(u"\u200B")

    # Output directory
    out_dir = arcpy.GetParameterAsText(10)

    # Current Python Project
    aprx = arcpy.mp.ArcGISProject('CURRENT')
    activeMap = aprx.activeMap

    for i in range(nr_of_outputs):
        # User endpoint and data from inference to create download link
        download_link = f"https://demo.sen2cube.at{str(output_url[i])}"

        # Get inference results
        with requests.Session() as s:
            s.headers.update(headers)
            outfile = s.get(download_link)

            # Create file name according to output type and name
            if output_type[i] == "geotiff":
                fname = f"{str(inference_id)}_{str(output_name[i])}.tiff"
            elif output_type[i] == "csv":
                fname = f"{str(inference_id)}_{str(output_name[i])}.csv"

            # Assemble complete path
            local_file = os.path.join(str(out_dir), fname)

            # Check if file already exists
            if os.path.exists(local_file):
                arcpy.AddMessage(
                    f"The file {str(fname)} already exists in the specified directory. The current file will be added as a new version.")
                # Create new versioned file name
                j = 1
                while True:
                    # Give new name
                    if output_type[i] == "geotiff":
                        fname_new = f"{str(inference_id)}_{str(output_name[i])}({str(j)}).tiff"
                    elif output_type[i] == "csv":
                        fname_new = f"{str(inference_id)}_{str(output_name[i])}({str(j)}).csv"
                    local_file_new = os.path.join(str(out_dir), fname_new)
                    if os.path.exists(local_file_new):
                        j = j + 1
                    else:
                        with open(local_file_new, 'wb') as f:
                            f.write(s.get(download_link, allow_redirects=True).content)
                        arcpy.AddMessage(
                            f"The output file {str(fname_new)} has been downloaded and stored at {str(out_dir)}.")
                        # Add Layer to Map
                        activeMap.addDataFromPath(local_file_new)
                        break
            else:
                local_file = os.path.join(str(out_dir), fname)
                with open(local_file, 'wb') as file:
                    file.write(s.get(download_link, allow_redirects=True).content)
                arcpy.AddMessage(f"The output file {str(fname)} has been downloaded and stored at {str(out_dir)}")
                # Adding Layer to Map
                activeMap.addDataFromPath(local_file)

        s.close()

    # Inform user
    arcpy.AddMessage('_________________')
    arcpy.AddMessage(u"\u200B")
    arcpy.AddMessage("Completed.")
    arcpy.AddMessage(u"\u200B")