# -*- coding: utf-8 -*-

import arcpy
from datetime import datetime, timedelta
import time
import threading
from processing_utils.geometry import validate_aoi
from processing_utils.sen2cube_requests import get_available_factbases
from processing_utils.sen2cube_requests import get_knowledgebases
from processing_utils.authentication import (get_access_token, 
                                             refresh_token)
from processing_utils.inference import (send_inference, 
                                        check_inference_status, 
                                        get_inference_results)


GLOBAL_VALS = {
    "logged_in": False,
    "token_object": None,
    "access_token" : None,
    "refresh_token" : None,
    "refresh_token_time" : None,
    "thread": None,
    "stop_event": threading.Event(),
    "all_factbase_data": None,
    "selected_factbase_data": None,
    "knowledgebases": None,
    # "login_counter": 0,
    # "refresh_counter": 0,
    # "other_counter": 0
}

BUFFER_SECONDS_UNTIL_TOKEN_EXPIRY = 15

class Toolbox: 
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Sen2Cube"
        self.alias = "Sen2Cube"

        # List of tool classes associated with this toolbox
        self.tools = [Sen2CubeTool]

 
class Sen2CubeTool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        
        self.label = "Sen2Cube Inference"
        self.description = "Authenticates the user in the Sen2Cube backend"

        # param indices (makes it easier to work with them, rather than always refering to the indices)
        self.USERNAME = 0
        self.PASSWORD = 1
        self.LOGIN_CHECKBOX = 2
        self.FACTBASE = 3
        self.KNOWLEDGEBASE = 4
        self.AOI = 5
        self.START_DATE = 6
        self.END_DATE = 7 
        self.COMMENT = 8
        self.FAVOURITE = 9
        self.QUICK_PREVIEW = 10
        self.OUTPUT_DIR = 11
        # self.INFO_DEBUG = 12
        # self.INFO_DEBUG1 = 13
        # self.INFO_DEBUG2 = 14


    def getParameterInfo(self):
        """Define the tool parameters."""
        
        params = [
            arcpy.Parameter(
                displayName="Username",
                name="user_name",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Password",
                name="password",
                datatype="GPStringHidden",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Login to sen2cube",
                name="login_button",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Currently Available Factbase",
                name="available_facebases",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Knowledgebase",
                name="knowledgebase",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Set the Area of Interest",
                name="aoi",
                datatype="GPExtent",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Start Date",
                name="start_date",
                datatype="GPDate",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="End Date",
                name="end_date",
                datatype="GPDate",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Add a comment to the inference",
                name="comment",
                datatype="GPString",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Save inference as favourite in sen2cube account",
                name="favourite",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Quick Preview (Downsamples factbase resolution)",
                name="quick_preview",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter(
                displayName="Output Directory",
                name="out_dir",
                datatype="DEFolder",
                parameterType="Required",
                direction="Input"
            ),
            # arcpy.Parameter(
            #     displayName="Info (Debug)",
            #     name="infodebug",
            #     datatype="GPString",
            #     parameterType="Optional",
            #     direction="Input"
            # ),
            # arcpy.Parameter(
            #     displayName="Info (Debug)1",
            #     name="infodebug1",
            #     datatype="GPString",
            #     parameterType="Optional",
            #     direction="Input"
            # ),
            # arcpy.Parameter(
            #     displayName="Info (Debug)2",
            #     name="infodebug2",
            #     datatype="GPString",
            #     parameterType="Optional",
            #     direction="Input"
            # )
            ]
        # initial states of the parameters
        params[self.FACTBASE].filter.type = "ValueList"
        params[self.KNOWLEDGEBASE].filter.type = "ValueList"
        # hide all parameters from factbase to output dir
        for idx in range(self.FACTBASE, (self.OUTPUT_DIR +1)):
            params[idx].enabled = False

 
        params[self.COMMENT].category = "Optional Settings" 
        params[self.FAVOURITE].category = "Optional Settings" 
        params[self.QUICK_PREVIEW].category = "Optional Settings" 
        # params[self.INFO_DEBUG].category = "Debugging" 
        # params[self.INFO_DEBUG1].category = "Debugging" 
        # params[self.INFO_DEBUG2].category = "Debugging" 

        
        return params


    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # attempt login
        if (parameters[self.LOGIN_CHECKBOX].value == True
            and GLOBAL_VALS["logged_in"] == False):

            self.updateMessages(parameters)

            # get token
            token, msg = get_access_token(username=parameters[self.USERNAME].valueAsText, 
                                          password=parameters[self.PASSWORD].valueAsText)
            if not token:
                arcpy.AddError(msg)
                return
            
            # ----------- START THREAD FOR TIME MONITORING AND TOKEN REFRESH -----------
            # set the token parameters
            GLOBAL_VALS["logged_in"] = True
            GLOBAL_VALS["token_object"] = token
            GLOBAL_VALS["access_token"] = token["access_token"]
            GLOBAL_VALS["refresh_token"] = token["refresh_token"]
            GLOBAL_VALS["refresh_token_time"] = token["expires_at"] - BUFFER_SECONDS_UNTIL_TOKEN_EXPIRY 
            # parameters[self.INFO_DEBUG].value = f"logged in (Nr. {GLOBAL_VALS['login_counter']}), refresh time: {GLOBAL_VALS['refresh_token_time']}" # debug
            self.start_thread_to_monitor_refresh_time(parameters)

            # ----------- GET ALL FACTBASE INFOS -----------
            # get factbase information from sen2cube.at
            all_factbase_data = get_available_factbases(GLOBAL_VALS["access_token"])
            GLOBAL_VALS["all_factbase_data"] = all_factbase_data
            available_factbases =  []
            for i in range(len(all_factbase_data['data'])):
                if all_factbase_data['data'][i]['attributes']['status'] == "OK":
                    available_factbases.append(all_factbase_data['data'][i]['attributes']['title'])

            # add the titles of available factbases to parameter drop-down list and make visible
            parameters[self.FACTBASE].filter.list = available_factbases
            
            # ----------- GET UESR KNOWLEDGEBASE MODELS -----------
            knowledgebases = get_knowledgebases(GLOBAL_VALS["access_token"])
            GLOBAL_VALS["knowledgebases"] = knowledgebases
            kb_titles = list(knowledgebases.keys())
            parameters[self.KNOWLEDGEBASE].filter.list = kb_titles
            
            # ----------- CHANGE PARAMETER VISIBILITY -----------
            parameters[self.USERNAME].enabled = False  
            parameters[self.PASSWORD].enabled = False
            parameters[self.LOGIN_CHECKBOX].enabled = False
            parameters[self.FACTBASE].enabled = True
            parameters[self.KNOWLEDGEBASE].enabled = True
            
            # GLOBAL_VALS["login_counter"] += 1  # debug

        # ----------- STORE SELECTED FACTBASE DATA -----------
        if parameters[self.FACTBASE].altered:
            selected_factbase = parameters[self.FACTBASE].valueAsText
            length = len(GLOBAL_VALS["all_factbase_data"]['data'])
            for i in range(length):
                if GLOBAL_VALS["all_factbase_data"]['data'][i]['attributes']['title'] == str(selected_factbase):
                    GLOBAL_VALS["selected_factbase_data"] = GLOBAL_VALS["all_factbase_data"]['data'][i]

            # and once the knowledge bases are loaded, also show all other parameters
            for idx in range(self.AOI, (self.OUTPUT_DIR +1)):
                parameters[idx].enabled = True


            
                         
        return


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        
        if parameters[self.LOGIN_CHECKBOX].altered:
            if not parameters[self.USERNAME].valueAsText:
                parameters[self.LOGIN_CHECKBOX].setErrorMessage("The username is still missing.")
                parameters[self.LOGIN_CHECKBOX].value = False
            elif not parameters[self.PASSWORD].valueAsText:
                parameters[self.LOGIN_CHECKBOX].setErrorMessage("The password ist still missing")
                parameters[self.LOGIN_CHECKBOX].value = False


        if parameters[self.START_DATE].altered: 
            
            # get allowed start and end dates
            start_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateStart"]
            allowed_start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateEnd"]
            allowed_end_date = datetime.strptime(end_str, "%Y-%m-%d") 

            input_start = str(parameters[self.START_DATE].value)
            input_start_date = self.parse_datetime_from_string(input_start)
            if input_start_date < allowed_start_date or input_start_date > allowed_end_date:
                parameters[self.START_DATE].setErrorMessage(f"Start date is out of range.\nThe available date range for this factbase is {str(start_str)} to {str(end_str)}.\nPlease adjust the start date.")
                
        if parameters[self.END_DATE].altered:
            
            # get allowed start and end dates
            start_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateStart"]
            allowed_start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateEnd"]
            allowed_end_date = datetime.strptime(end_str, "%Y-%m-%d")

            input_end = str(parameters[self.END_DATE].value)
            input_end_date = self.parse_datetime_from_string(input_end)
            if input_end_date < allowed_start_date or input_end_date > allowed_end_date:
                parameters[self.END_DATE].setErrorMessage(f"End date is out of range.\nThe available date range for this factbase is {str(start_str)} to {str(end_str)}.\nPlease adjust the start date.")
            if str(parameters[self.START_DATE].value) != "":
                input_start = str(parameters[self.START_DATE].value)
                input_start_date = self.parse_datetime_from_string(input_start)
                if input_end_date < input_start_date:
                    parameters[self.START_DATE].setErrorMessage(f"The selected end date is before the start date.\nPlease adjust the dates.")
                    parameters[self.END_DATE].setErrorMessage(f"The selected end date is before the start date.\nPlease adjust the dates.")

        # Check AOI is within Factbase via "select by location"
        if parameters[self.AOI].altered:
 
            aoi_extent = parameters[self.AOI].value
            # if the user reset the AOI - the values are 0,0,0,0
            xmin, ymin, xmax, ymax = aoi_extent.XMin, aoi_extent.YMin, aoi_extent.XMax, aoi_extent.YMax
            if (xmin != 0 
                and ymin != 0
                and xmax != 0
                and ymax != 0):
                factbase_geojson_geometry = GLOBAL_VALS["selected_factbase_data"]["attributes"]["footprint"]["features"][0]["geometry"]
                factbase_srs = GLOBAL_VALS["selected_factbase_data"]["attributes"]["srs"]
                valid_extent = validate_aoi(aoi_extent, factbase_geojson_geometry, factbase_srs)
                # parameters[self.INFO_DEBUG1].value = valid_extent
                if valid_extent == False:
                    parameters[self.AOI].setErrorMessage(f"The entered extent doesn't intersect with the geometry of the selected factbase ({parameters[self.FACTBASE].valueAsText}). Please adjust the extent.")
 
        # Check AOI is contain, overlaps or is within the Factbase
        if parameters[self.FACTBASE].altered:
            # only check if the user has changed the AOI/extent
            if parameters[self.AOI].value != None:
                aoi_extent = parameters[self.AOI].value
                # only check if the AOI isn't reset (in which cse the values are 0,0,0,0)
                xmin, ymin, xmax, ymax = aoi_extent.XMin, aoi_extent.YMin, aoi_extent.XMax, aoi_extent.YMax
                if (xmin != 0 
                    and ymin != 0
                    and xmax != 0
                    and ymax != 0):
                    factbase_geojson_geometry = GLOBAL_VALS["selected_factbase_data"]["attributes"]["footprint"]["features"][0]["geometry"]
                    factbase_srs = GLOBAL_VALS["selected_factbase_data"]["attributes"]["srs"]
                    valid_extent = validate_aoi(aoi_extent, factbase_geojson_geometry, factbase_srs)
                    # parameters[self.INFO_DEBUG1].value = valid_extent
                    if valid_extent == False:
                        parameters[self.AOI].setErrorMessage(f"The entered extent doesn't intersect with the geometry of the selected factbase ({parameters[self.FACTBASE].valueAsText}). Please adjust the extent.")

        return
    

    def execute(self, parameters, messages):
        """
        This is the bit that happens when the user clicks run.
        - Sends the query to sen2cube
        - Gets result
        - Loads into ArcGIS Pro
        """

        username = parameters[self.USERNAME].valueAsText
        fb_id = GLOBAL_VALS["selected_factbase_data"]["id"]
        selected_kb = parameters[self.KNOWLEDGEBASE].valueAsText
        kb_id = GLOBAL_VALS["knowledgebases"][selected_kb]
        extent_points = parameters[self.AOI].value
        input_start = str(parameters[self.START_DATE].value)
        input_start_date = self.parse_datetime_from_string(input_start)
        start_date = input_start_date.strftime("%Y-%m-%dT23:59:59.999Z")
        input_end = str(parameters[self.END_DATE].value)
        input_end_date = self.parse_datetime_from_string(input_end)
        end_date = input_end_date.strftime("%Y-%m-%dT23:59:59.999Z")
        comment = parameters[self.COMMENT].valueAsText
        favorite = parameters[self.FAVOURITE].value
        quick_preview = parameters[self.QUICK_PREVIEW].value
        output_dir = parameters[self.OUTPUT_DIR].valueAsText

        inference_id = send_inference(access_token=GLOBAL_VALS["access_token"],
                                    username=username,
                                    fb_id=fb_id,
                                    kb_id=kb_id,
                                    extent_points=extent_points,
                                    start_date=start_date,
                                    end_date=end_date,
                                    comment=comment,
                                    favorite=favorite,
                                    quick_preview=quick_preview)

        # Inform user
        arcpy.AddMessage(f"Inference created. ID: {str(inference_id)}\n")
        arcpy.AddMessage(u"\u200B")
        arcpy.AddMessage("The request is now being processed by Sen2Cube. This process may take up to a few minutes.")
        arcpy.AddMessage("Do not terminate the tool during this time, otherwise the inference will not be loaded into the map.")
        arcpy.AddMessage(u"\u200B")

        status = "-"
        while status != "SUCCEEDED":
            status, msg = check_inference_status(status, 
                                                 access_token=GLOBAL_VALS["access_token"], 
                                                 inference_id=inference_id)
            arcpy.AddMessage(msg)
            time.sleep(10)

        get_inference_results(access_token=GLOBAL_VALS["access_token"],
                              inference_id=inference_id,
                              output_dir=output_dir)
        

        return


    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""

        # log out? 

        return



    def parse_datetime_from_string(self, input_datetime_string): 

        # maybe add more formats?

        try:
            parsed_date = datetime.strptime(input_datetime_string, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            parsed_date = datetime.strptime(input_datetime_string, "%Y-%m-%d %H:%M:%S")

        return parsed_date
    
    
    def thread_to_monitor_refresh_time(self, parameters):
        """
        Monitors when the token needs to be refreshed and updates it automatically.
        """
        while GLOBAL_VALS["logged_in"] == True:
            now = datetime.now().timestamp()
            if now >= GLOBAL_VALS["refresh_token_time"]:
                new_token, msg = refresh_token(token=GLOBAL_VALS["token_object"])
                if new_token:
                    # GLOBAL_VALS["refresh_counter"] += 1
                    GLOBAL_VALS['token_object'] = new_token
                    GLOBAL_VALS['access_token'] = new_token["access_token"]
                    GLOBAL_VALS['refresh_token'] = new_token["refresh_token"]
                    time_to_refresh = new_token["expires_at"] - BUFFER_SECONDS_UNTIL_TOKEN_EXPIRY
                    GLOBAL_VALS["refresh_token_time"] = time_to_refresh
                    # parameters[self.INFO_DEBUG1].value = f"REFRESHED (Nr {GLOBAL_VALS['refresh_counter']})."
                else:
                    GLOBAL_VALS["logged_in"] = False
                    arcpy.AddMessage(f"Could not refresh your authentication with sen2cube: {msg}.")
                    self.stop_thread_to_monitor_refresh_time()
            # else:
                # parameters[self.INFO_DEBUG2].value = f"Still waiting to refresh at {GLOBAL_VALS['refresh_token_time']}. Now is: {now}"  # Debug
            
            time.sleep(5)  # Only check every 5 seconds to avoid excessive CPU use
            # parameters[self.INFO_DEBUG].value = f"other counter: {GLOBAL_VALS['other_counter']}"
            # GLOBAL_VALS["other_counter"] += 1


    def start_thread_to_monitor_refresh_time(self, parameters):
        """Starts the token monitoring in a new thread."""
        if GLOBAL_VALS["thread"] is None:
            GLOBAL_VALS["stop_event"].clear()  # Reset the stop event
            GLOBAL_VALS["thread"] = threading.Thread(target=self.thread_to_monitor_refresh_time, args=(parameters,))
            GLOBAL_VALS["thread"].daemon = True  # Ensures the thread stops when the main program exits
            GLOBAL_VALS["thread"].start()


    def stop_thread_to_monitor_refresh_time(self):
        """Stops the token monitoring thread."""
        if GLOBAL_VALS["thread"] and GLOBAL_VALS["thread"].is_alive():
            GLOBAL_VALS["stop_event"].set()  # Signal the thread to stop
            GLOBAL_VALS["thread"].join()  # Wait for the thread to exit