import arcpy
from arcpy import *
import sys
import os
import json
import requests
from arcgis.geometry import Point, Polyline, Polygon, Geometry
from arcgis.gis import GIS
from arcgis.geocoding import geocode
from arcgis.geometry import lengths, areas_and_lengths, project
import requests_oauthlib
import oauthlib
import time

from datetime import datetime, date, timedelta
from oauthlib.oauth2 import InvalidGrantError, LegacyApplicationClient, OAuth2Token, \
    UnauthorizedClientError
from requests import Response
from requests_oauthlib import OAuth2Session


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


def get_fb(token_text):
    fb_list = 'https://api.sen2cube.at/v1/factbase'
    headers = {'Authorization': 'Bearer {}'.format(token_text['access_token'])}
    with requests.Session() as s:
        s.headers.update(headers)
        fb_result = s.get(fb_list).json()
        now = datetime.utcnow()

    return fb_result, now


class ToolValidator:
    # Class to add custom behavior and properties to the tool and tool parameters.
    global fb_result

    def __init__(self):
        # set self.params for use in other function
        self.params = arcpy.GetParameterInfo()

        # Set map projection such that footprints show up
        wgs84 = arcpy.SpatialReference(4326)
        activeMap = arcpy.mp.ArcGISProject("CURRENT").activeMap
        map_reference_code = activeMap.spatialReference.PCSCode
        original = arcpy.SpatialReference(map_reference_code)
        if not activeMap.spatialReference == wgs84:
            activeMap.spatialReference = wgs84

    def initializeParameters(self):
        # Customize parameter properties.
        # This gets called when the tool is opened.
        return

    def updateParameters(self):
        # Modify parameter values and properties.
        # This gets called each time a parameter is modified, before
        # standard validation.

        # --------------------------------  Links needed for get requests --------------------------------------------

        auth_token_url = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/token"
        auth_client_id = "iq-web-client"
        # fb_list = 'https://api.sen2cube.at/v1/factbase'
        kb_list = 'https://api.sen2cube.at/v1/knowledgebase'
        # Scratch DB for temporary Layers (e.g. AOI or BBOX of Factbases)
        db_path = arcpy.mp.ArcGISProject("CURRENT").defaultGeodatabase
        # Current Project
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        # Active Map
        activeMap = arcpy.mp.ArcGISProject("CURRENT").activeMap
        # Spatial Reference of Map
        map_reference_code = activeMap.spatialReference.PCSCode
        # Arcpy formatted spatial reference
        map_spatial_reference = arcpy.SpatialReference(map_reference_code)

        global fb_result
        global selected_fb

        # -------------------------------------------  LOGIN  --------------------------------------------------------

        # If the Login box hasn't been checked, hide all other parameters
        if not self.params[2].value == True:
            self.params[3].enabled = False  # Factbase
            self.params[4].enabled = False  # Knowledgebase
            self.params[5].enabled = False  # AOI
            self.params[6].enabled = False  # Start Date
            self.params[7].enabled = False  # End Date
            self.params[8].enabled = False  # Comment
            self.params[9].enabled = False  # Favourite
            self.params[10].enabled = False  # Output Directory

        # If login box checked, get entered parameters from user
        if self.params[2].value == True:
            username = self.params[0].value
            password = self.params[1].value

            # ---------------------------------------  GET TOKEN  ----------------------------------------------------

            # Get token with user's input
            token_text = fetch_token(username, password, auth_token_url, auth_client_id)
            if token_text:
                # If login successful, hide login parameters
                self.params[0].enabled = False  # Username
                self.params[1].enabled = False  # Password
                self.params[2].enabled = False  # Checkbox

                # ------------------------------------ FILL FACTBASE VALUES  -----------------------------------------

                entries = []

                fb_result, now = get_fb(token_text)
                # Subtract 300 seconds to the time that was gotten in the same moment as the factbase list
                now_minus300secs = now - timedelta(seconds=300)

                # Only take the titles of those factbases where busy ping or free ping was less than 300 secs ago
                for i in range(len(fb_result['data'])):
                    # Get pings from JSON
                    busy_worker = fb_result['data'][i]['attributes']['busy_worker_ping']
                    free_worker = fb_result['data'][i]['attributes']['free_worker_ping']
                    # Turn into python time values
                    check_busy = datetime.strptime(busy_worker, "%Y-%m-%dT%H:%M:%S.%f+00:00")
                    check_free = datetime.strptime(free_worker, "%Y-%m-%dT%H:%M:%S.%f+00:00")

                    # Check if either the free ping or the busy ping was within the last 300 seconds
                    if check_free > now_minus300secs:
                        entries.append(fb_result['data'][i]['attributes']['title'])
                    elif check_busy > now_minus300secs:
                        entries.append(fb_result['data'][i]['attributes']['title'])

                # Add any "online" factbase titles to parameter drop-down list
                if len(entries) > 0:
                    self.params[3].filter.list = entries
                    # Make Factbase parameter visible
                    self.params[3].enabled = True
                else:
                    self.params[3].value = "n/a"
                    self.params[3].enabled = True
                    # sys.exit(0)

        # ------------------------------------ FILL KNOWLEDGEBASE VALUES  -----------------------------------------

        # If a Factbase is selected
        if self.params[3].altered:

            if self.params[3].value == "n/a":
                pass

            else:
                # Get list of Knowledgebases
                titles = []
                # Send Get Request
                headers = {'Authorization': 'Bearer {}'.format(token_text['access_token'])}
                payload = {'page[size]': 0}	
                with requests.Session() as s:
                    s.headers.update(headers)
                    kb_result = s.get(kb_list, params=payload).json()	
                    
                    # Get all titles
                    for j in range(len(kb_result['data'])):
                        titles.append(kb_result['data'][j]['attributes']['title'])

                    # Add titles to parameter drop-down list
                    titles.sort()
                    self.params[4].filter.list = titles

                # Show all other parameters now
                self.params[4].enabled = True  # Knowledgebase
                self.params[5].enabled = True  # AOI
                self.params[6].enabled = True  # Start Date
                self.params[7].enabled = True  # End Date
                self.params[8].enabled = True  # Comment
                self.params[9].enabled = True  # Favourite
                self.params[10].enabled = True  # Output Directory

                # Chosen Factbase
                selected_fb = self.params[3].value

                # ----------------------------- SHOW FACTBASE FOOTPRINT IN MAP -----------------------------------------

                # File Name and Path to Scratch DB
                fp_line_path = os.path.join(str(db_path), "temp")

                # Handle Whitespace in name for Syria
                if str(selected_fb) == "North-Western Syria":
                    name = "Syria_Factbase_Footprint"
                else:
                    name = f"{str(selected_fb)}_Factbase_Footprint"

                fp_poly_path = os.path.join(str(db_path), name)

                # If the selected Factbase Footprint already exists - pass
                if arcpy.Exists(fp_poly_path):
                    pass
                else:
                    check_syria = os.path.join(str(db_path), "Syria_Factbase_Footprint")
                    check_austria = os.path.join(str(db_path), "Austria_Factbase_Footprint")
                    check_afghanistan = os.path.join(str(db_path), "Afghanistan_Factbase_Footprint")
                    check_semantix = os.path.join(str(db_path), "Semantix_Factbase_Footprint")

                    # Delete any other Factbase Footprint
                    if str(selected_fb) == "Austria":
                        if arcpy.Exists(check_semantix):
                            arcpy.Delete_management(check_semantix)
                        if arcpy.Exists(check_syria):
                            arcpy.Delete_management(check_syria)
                        if arcpy.Exists(check_afghanistan):
                            arcpy.Delete_management(check_afghanistan)

                    elif str(selected_fb) == "North-Western Syria":
                        if arcpy.Exists(check_semantix):
                            arcpy.Delete_management(check_semantix)
                        if arcpy.Exists(check_austria):
                            arcpy.Delete_management(check_austria)
                        if arcpy.Exists(check_afghanistan):
                            arcpy.Delete_management(check_afghanistan)

                    elif str(selected_fb) == "Afghanistan":
                        if arcpy.Exists(check_semantix):
                            arcpy.Delete_management(check_semantix)
                        if arcpy.Exists(check_syria):
                            arcpy.Delete_management(check_syria)
                        if arcpy.Exists(check_austria):
                            arcpy.Delete_management(check_austria)

                    elif str(selected_fb) == "SemantiX":
                        if arcpy.Exists(check_austria):
                            arcpy.Delete_management(check_austria)
                        if arcpy.Exists(check_syria):
                            arcpy.Delete_management(check_syria)
                        if arcpy.Exists(check_afghanistan):
                            arcpy.Delete_management(check_afghanistan)

                    for i in range(len(fb_result['data'])):
                        if fb_result['data'][i]['attributes']['title'] == str(selected_fb):
                            # Get Footprint of Factbase
                            footprint = fb_result['data'][i]['attributes']['footprint']['features'][0]['geometry'][
                                'coordinates']

                    reproj_points2 = []
                    footprint_array = arcpy.Array()

                    # Getting the array of coordinates from the JSON from Sen2Cube - Each factbase handled individually
                    # because each data format different (amount of square brackets)
                    if str(selected_fb) == "Austria":
                        for point in footprint[1][0]:
                            # Create arcpy.Points and add to Array
                            footprint_array.append(arcpy.Point(point[0], point[1]))

                    elif str(selected_fb) == "North-Western Syria":
                        for point in footprint[0][0]:
                            # Create arcpy.Points and add to Array
                            footprint_array.append(arcpy.Point(point[0], point[1]))

                    elif str(selected_fb) == "Afghanistan":
                        for point in footprint[0][0]:
                            # Create arcpy.Points and add to Array
                            footprint_array.append(arcpy.Point(float(point[0]), float(point[1])))

                    elif str(selected_fb) == "SemantiX":
                        for point in footprint[0]:
                            # Create arcpy.Points and add to Array
                            footprint_array.append(arcpy.Point(point[0], point[1]))

                    for point in footprint_array:
                        pnt_geometry = arcpy.PointGeometry(point, map_spatial_reference)
                        projectedPointGeometry = pnt_geometry.projectAs(arcpy.SpatialReference(4326))
                        reproj_points2.append(projectedPointGeometry)

                    # Points to Line
                    arcpy.PointsToLine_management(reproj_points2, fp_line_path)
                    # Line to Polygon
                    arcpy.management.FeatureToPolygon(fp_line_path, fp_poly_path)
                    # Delete temp layer
                    arcpy.Delete_management(fp_line_path)
                    # Add to Map
                    activeMap.addDataFromPath(fp_poly_path)

                    layers = activeMap.listLayers()
                    for layer in layers:
                        if layer.name == name:
                            if layer.supports("TRANSPARENCY"):
                                layer.transparency = 60

        # ------------------------------------ SHOW SELECTED AOI IN MAP -----------------------------------------

        # If AOI Extent altered, check if the extent is new or has changed and display on map
        if self.params[5].altered:

            # "createNewAOI" is used to check if there is already an AOI shown, and if the extent has changed
            global createNewAOI, allowed_start
            createNewAOI = "yes"

            # Get Input Extent and split into its individual units
            individual_units = str(self.params[5].value).split()

            # File Name and Path to Scratch DB
            filename = "Your_AOI"
            layer_path = os.path.join(str(db_path), filename)

            # If a "Your_AOI" already exists, check if extent is same, else delete and replace
            if arcpy.Exists(layer_path):

                # Get Current Extent
                filenameNew = "YourAOI"
                layer_pathNew = os.path.join(str(db_path), filenameNew)
                points1 = []
                reproj_points1 = []

                # Remove commas if present and only use first 4 since those are the coordinates for BBOX
                for i in range(4):
                    points1.append(individual_units[i].replace(",", "."))

                # Create arcpy.Points and add to Array
                pointsArray = arcpy.Array([arcpy.Point(float(points1[0]), float(points1[1])),
                                           arcpy.Point(float(points1[2]), float(points1[1])),
                                           arcpy.Point(float(points1[2]), float(points1[3])),
                                           arcpy.Point(float(points1[0]), float(points1[3])),
                                           arcpy.Point(float(points1[0]), float(points1[1]))])

                for point in pointsArray:
                    pnt_geometry = arcpy.PointGeometry(point, map_spatial_reference)
                    projectedPointGeometry = pnt_geometry.projectAs(arcpy.SpatialReference(4326))
                    reproj_points1.append(projectedPointGeometry)

                # Points to Line
                arcpy.PointsToLine_management(reproj_points1, layer_pathNew)

                # Describe the new Extent and the old Extent
                desc = arcpy.Describe(layer_pathNew)
                desc1 = arcpy.Describe(layer_path)
                extent = [desc.extent.XMin, desc.extent.XMax, desc.extent.YMin, desc.extent.YMax]
                extent1 = [desc1.extent.XMin, desc1.extent.XMax, desc1.extent.YMin, desc1.extent.YMax]

                # Check if the extents are the same
                if extent == extent1:
                    # If same, no need to replace the AOI
                    createNewAOI = "no"
                # If not the same, delete old one and create new one
                else:
                    arcpy.Delete_management(layer_path)
                    createNewAOI = "yes"

                # Delete temporary extent layer in any case (was only for comparison)
                arcpy.Delete_management(layer_pathNew)

            if createNewAOI == "yes":
                points = []
                reproj_points = []

                # Remove commas if present and only use first 4 since those are the coordinates for BBOX
                for i in range(4):
                    points.append(individual_units[i].replace(",", "."))

                # Create arcpy.Points and add to Array
                pointsArray = arcpy.Array([arcpy.Point(float(points[0]), float(points[1])),
                                           arcpy.Point(float(points[2]), float(points[1])),
                                           arcpy.Point(float(points[2]), float(points[3])),
                                           arcpy.Point(float(points[0]), float(points[3])),
                                           arcpy.Point(float(points[0]), float(points[1]))])

                for point in pointsArray:
                    pnt_geometry = arcpy.PointGeometry(point, map_spatial_reference)
                    projectedPointGeometry = pnt_geometry.projectAs(arcpy.SpatialReference(4326))
                    reproj_points.append(projectedPointGeometry)

                # Points to Line
                arcpy.PointsToLine_management(reproj_points, layer_path)

                # Add to Map
                activeMap.addDataFromPath(layer_path)

            return

    def updateMessages(self):
        # Customize messages for the parameters.
        # This gets called after standard validation.

        if self.params[3].value == "n/a":
            self.params[3].setErrorMessage("No factbases are currently online. Please try again at a later time.")

        if self.params[2].value == True:
            auth_token_url = "https://auth.sen2cube.at/realms/sen2cube-at/protocol/openid-connect/token"
            auth_client_id = "iq-web-client"
            username = self.params[0].value
            password = self.params[1].value
            token_text = fetch_token(username, password, auth_token_url, auth_client_id)

            global fb_result
            fb_result, now = get_fb(token_text)

            global allowed_start
            global allowed_end

            selected_fb = self.params[3].value

            # ------------------------------------ CHECKS FOR DATE RANGE -----------------------------------------

            # Date format in Sen2Cube JSON: 2021-01-28
            # Date format from user input: 2022-02-02 20:09:08

        # Start Date
        if self.params[6].altered:
            length = len(fb_result['data'])
            for i in range(length):
                if fb_result['data'][i]['attributes']['title'] == str(selected_fb):
                    # Get valid date range from factbase
                    fb_start = fb_result['data'][i]['attributes']['dateStart']
                    allowed_start = datetime.strptime(fb_start, "%Y-%m-%d")
                    fb_end = fb_result['data'][i]['attributes']['dateEnd']
                    allowed_end = datetime.strptime(fb_end, "%Y-%m-%d")
                    # Get user input
                    input_start = str(self.params[6].value)
                    start = datetime.strptime(input_start, "%Y-%m-%d %H:%M:%S")
                    # If the entered date is either before or after the factbase's valid range, set Error Message
                    if start < allowed_start or allowed_end < start:
                        self.params[6].setErrorMessage(
                            f"\nInvalid Start Date.\n\nThe valid date range for this Factbase is {str(allowed_start.strftime('%Y-%m-%d'))} to {str(allowed_end.strftime('%Y-%m-%d'))}. Please adjust the date.")

        # End Date
        if self.params[7].altered:
            length = len(fb_result['data'])
            for i in range(length):
                if fb_result['data'][i]['attributes']['title'] == str(selected_fb):
                    # Get valid date range from factbase
                    fb_start = fb_result['data'][i]['attributes']['dateStart']
                    allowed_start = datetime.strptime(fb_start, "%Y-%m-%d")
                    fb_end = fb_result['data'][i]['attributes']['dateEnd']
                    allowed_end = datetime.strptime(fb_end, "%Y-%m-%d")
                    # Get user input
                    input_end = str(self.params[7].value)
                    end = datetime.strptime(input_end, "%Y-%m-%d %H:%M:%S")
                    input_start = str(self.params[6].value)
                    start = datetime.strptime(input_start, "%Y-%m-%d %H:%M:%S")
                    # If the entered date is either before or after the factbase's valid range, set Error Message
                    if allowed_end < end or end < allowed_start:
                        self.params[7].setErrorMessage(
                            f"\nInvalid End Date.\n\nThe valid date range for this Factbase is {str(allowed_start.strftime('%Y-%m-%d'))} to {str(allowed_end.strftime('%Y-%m-%d'))}. Please adjust the date.")

                    # If the entered end date is before the entered start date
                    if start:
                        if end < start:
                            self.params[7].setErrorMessage(
                                "The selected end date is before the selected start date. Please change the dates.")

        # ---------------------------------- CHECK AOI INTERSECTS WITH FACTBASE ---------------------------------------

        # Check AOI is within Factbase via "select by location"
        if self.params[5].altered:

            # Get Factbase Layer Name
            selected_fb = self.params[3].value
            if str(selected_fb) == "North-Western Syria":
                name = "Syria_Factbase_Footprint"
            else:
                name = f"{str(selected_fb)}_Factbase_Footprint"

            # Select if intersects and add to variable "check_aoi"
            check_aoi = arcpy.SelectLayerByLocation_management('Your_AOI', 'INTERSECT', name)
            # Count amount of features in variable
            count = int(arcpy.GetCount_management(check_aoi)[0])
            # Add error message if 0 (= no features intersect)
            if count == 0:
                self.params[5].setErrorMessage("The chosen Area of Interest does not overlap with the footprint of the selected Factbase. Please adjust the Area of Interest.")
            # Clear Selection
            arcpy.management.SelectLayerByAttribute(check_aoi, 'CLEAR_SELECTION')

        return

    # def isLicensed(self):
    #     # set tool isLicensed.
    # return True
