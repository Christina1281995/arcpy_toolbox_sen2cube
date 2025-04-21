# -*- coding: utf-8 -*-

import arcpy
from datetime import datetime, timedelta
import time
import threading
from processing_utils.geometry import validate_aoi
from processing_utils.sen2cube_requests import get_available_factbases
from processing_utils.sen2cube_requests import get_knowledgebases
from processing_utils.authentication import (get_access_token, 
                                             refresh_token,
                                             get_preferred_username)
from processing_utils.inference import (send_inference, 
                                        check_inference_status, 
                                        get_inference_results)


GLOBAL_VALS = {
    "logged_in": False,
    "token_object": None,
    "access_token" : None,
    "refresh_token" : None,
    "refresh_token_time" : None,
    "thread_refresh": None,
    "stop_event_refresh": threading.Event(),
    "thread_inactivity": None,
    "last_activity_time": None, 
    "stop_event_inactivity": threading.Event(),
    "inference_running": False,
    "all_factbase_data": None,
    "selected_factbase_data": None,
    "knowledgebases": None,
    "username": None
    # "login_counter": 0,
    # "refresh_counter": 0,
    # "other_counter": 0
}

DEBUGGING_TXT_FILE = r"C:/Users/chris/Documents/GitHub Repos/arcpy_toolbox_sen2cube/pythontoolbox/debugging.txt"
TOKEN_DEBUGGING_TXT_FILE = r"C:/Users/chris/Documents/GitHub Repos/arcpy_toolbox_sen2cube/pythontoolbox/token_debugging.txt"
AUTO_LOGOUT_SECONDS = 60
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
        self.HIDDEN_LOGIN_ERROR_MESSAGE = 12
        self.INACTIVITY_RESET = 13
        self.JUST_RESET = 14


    def getParameterInfo(self):
        """Define the tool parameters."""
        
        params = [
            arcpy.Parameter( #0
                displayName="Username",
                name="user_name",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #1
                displayName="Password",
                name="password",
                datatype="GPStringHidden",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #2
                displayName="Login to sen2cube",
                name="login_button",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #3
                displayName="Currently Available Factbase",
                name="available_facebases",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #4
                displayName="Knowledgebase",
                name="knowledgebase",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #5
                displayName="Set the Area of Interest",
                name="aoi",
                datatype="GPExtent",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #6
                displayName="Start Date",
                name="start_date",
                datatype="GPDate",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #7
                displayName="End Date",
                name="end_date",
                datatype="GPDate",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #8
                displayName="Add a comment to the inference",
                name="comment",
                datatype="GPString",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #9
                displayName="Save inference as favourite in sen2cube account",
                name="favourite",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #10
                displayName="Quick Preview (Downsamples factbase resolution)",
                name="quick_preview",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #11
                displayName="Output Directory",
                name="out_dir",
                datatype="DEFolder",
                parameterType="Required",
                direction="Input"
            ),
            arcpy.Parameter( #12
                displayName="Login Monitoring",
                name="hidden_login_err_msg",
                datatype="GPString",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #13
                displayName="Inactivity Reset",
                name="inactivity_reset",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            arcpy.Parameter( #14
                displayName="Just Reset",
                name="just_reset",
                datatype="GPBoolean",
                parameterType="Optional",
                direction="Input"
            ),
            # arcpy.Parameter( #15
            #     displayName="Info (Debug)",
            #     name="infodebug",
            #     datatype="GPString",
            #     parameterType="Optional",
            #     direction="Input"
            # ),
            # arcpy.Parameter( #16
            #     displayName="Info (Debug)1",
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

        # add all optional parameters to one collapsible category
        params[self.COMMENT].category = "Optional Settings" 
        params[self.FAVOURITE].category = "Optional Settings" 
        params[self.QUICK_PREVIEW].category = "Optional Settings" 

        # these parameters are for internal tool state handling 
        # and should not be shown
        params[self.HIDDEN_LOGIN_ERROR_MESSAGE].enabled = False
        params[self.INACTIVITY_RESET].enabled = False
        params[self.JUST_RESET].enabled = False
         
        return params


    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True


    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # update 'last activity time' every time an interaction with the GUI happens 
        #    -> GUI interaction automatically calls this updateParameters function
        GLOBAL_VALS["last_activity_time"] = datetime.now().timestamp()

        # ------------ LOGIN --------------

        # the login checkbox is only enabled at the beginning, when the tool is opened 
        # so, if the user had previously logged in, but then opens the tool again, the user should have to login again
        # therefore: set logged in variable to false
        if parameters[self.LOGIN_CHECKBOX].enabled:
            GLOBAL_VALS["logged_in"] = False
    
        # when the user changes the values for the username or password, 
        # the tool clears any previous error messages (related to either missing parameters or 
        # failed login attempts) --> this enables a new login attempt with the changed values
        if parameters[self.USERNAME].altered or parameters[self.PASSWORD].altered:
            parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].value = ""
            parameters[self.LOGIN_CHECKBOX].clearMessage()

        # attempt login
        if parameters[self.LOGIN_CHECKBOX].value == True:

            # call updateMessages() to set error messages if one of the 
            # input params is still missing (i.e. no username or password supplied)
            self.updateMessages(parameters)

            # don't proceed with login attempt if any error messages were set
            if parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].valueAsText != None:
                if len(parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].valueAsText) > 0:
                    return

            # try to get access token
            token, msg = get_access_token(username=parameters[self.USERNAME].valueAsText, 
                                          password=parameters[self.PASSWORD].valueAsText)
            
            # in case of failure to get access token:
            #    add the error message to the hidden parameter and then 
            #    use that value to display the error message at the login checkbox
            #    (in the arcgis pro python toolbox it's not possible to trigger the .setErrorMessage() function
            #    programmatically, so altering a hidden parameter is the best option)
            if not token:
                parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].value = str(msg)
                self.updateMessages(parameters)
                return
            
            # ----------- SET GLOBAL VALUES (ACCESSIBLE TO OTHER FUNCTIONS) -----------
            GLOBAL_VALS["username"] = parameters[self.USERNAME].valueAsText
            GLOBAL_VALS["logged_in"] = True
            GLOBAL_VALS["token_object"] = token
            GLOBAL_VALS["access_token"] = token["access_token"]
            GLOBAL_VALS["refresh_token"] = token["refresh_token"]
            GLOBAL_VALS["refresh_token_time"] = token["expires_at"] - BUFFER_SECONDS_UNTIL_TOKEN_EXPIRY

            # get user's preferred username (for "owner" label in inference) 
            user_info = get_preferred_username(GLOBAL_VALS["access_token"])
            GLOBAL_VALS["preferred_username"] = user_info["preferred_username"]
            
            # ----------- START THREADS FOR TIME MONITORING AND TOKEN REFRESH -----------
            self.start_thread_to_monitor_token_refresh_time()
            self.start_thread_to_monitor_inactivity_time(parameters)


            # ----------- GET ALL FACTBASE INFOS -----------
            all_factbase_data = get_available_factbases(GLOBAL_VALS["access_token"])
            GLOBAL_VALS["all_factbase_data"] = all_factbase_data
            available_factbases =  []
            for i in range(len(all_factbase_data['data'])):
                if all_factbase_data['data'][i]['attributes']['status'] == "OK":
                    available_factbases.append(all_factbase_data['data'][i]['attributes']['title'])

            # add the titles of available factbases to parameter drop-down list and make visible
            parameters[self.FACTBASE].filter.list = available_factbases
            
            # ----------- GET UESR'S KNOWLEDGEBASE MODELS -----------
            knowledgebases = get_knowledgebases(GLOBAL_VALS["access_token"])
            GLOBAL_VALS["knowledgebases"] = knowledgebases
            kb_titles = list(knowledgebases.keys())
            parameters[self.KNOWLEDGEBASE].filter.list = kb_titles
            
            # ----------- CHANGE PARAMETER VISIBILITY -----------
            parameters[self.USERNAME].enabled = False  
            parameters[self.PASSWORD].enabled = False
            parameters[self.LOGIN_CHECKBOX].value = False
            parameters[self.LOGIN_CHECKBOX].enabled = False
            parameters[self.FACTBASE].enabled = True
            parameters[self.KNOWLEDGEBASE].enabled = True
            return
        

        # ---------- RETURN TO LOGIN IF INACTIVE FOR TOO LONG ---------

        # these conditions are checked each time the user interacts with the GUI
        # so the inactivity-based logout will only "show" when the user returns to the 
        # tool after being inactive for some time
 
        # Either one of the Threads can set the logged_in variable to False 
        #    -> either through inactivity for too long
        #    -> or if the token refresh didn't work
        if (GLOBAL_VALS["logged_in"] == "False" 
            and not parameters[self.LOGIN_CHECKBOX].enabled):

            parameters[self.INACTIVITY_RESET].value = True
        
        if parameters[self.INACTIVITY_RESET].value == True:
            
            # GLOBAL_VALS["stop_event_inactivity"].set()
            self.stop_thread_to_monitor_inactivity()
            self.stop_thread_to_monitor_refresh_time()

            with open(DEBUGGING_TXT_FILE, "a") as f:
                f.write(f"\n- Identified that the inactivity reset box is TRUE...")
            for idx in range(self.FACTBASE, (self.OUTPUT_DIR +1)):
                parameters[idx].enabled = False
                parameters[idx].value = None

            parameters[self.USERNAME].value = GLOBAL_VALS["username"]
            parameters[self.USERNAME].enabled = True            
            parameters[self.PASSWORD].value = None
            parameters[self.PASSWORD].enabled = True            
            parameters[self.LOGIN_CHECKBOX].value = False
            parameters[self.LOGIN_CHECKBOX].enabled = True

            # lastly, reset the inactivity reset button back to false
            parameters[self.INACTIVITY_RESET].value = False
            parameters[self.JUST_RESET].value = True
            return
        
        # ----------- STORE SELECTED FACTBASE DATA -----------
        if parameters[self.FACTBASE].altered and parameters[self.FACTBASE].value != None:
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

        # check if both username and password were entered
        if (parameters[self.LOGIN_CHECKBOX].altered 
            and (parameters[self.JUST_RESET].value == False
                 or parameters[self.JUST_RESET].value == None)):
            if not parameters[self.USERNAME].valueAsText:
                parameters[self.LOGIN_CHECKBOX].setErrorMessage("The username is still missing.")
                parameters[self.LOGIN_CHECKBOX].value = False
            elif not parameters[self.PASSWORD].valueAsText:
                parameters[self.LOGIN_CHECKBOX].setErrorMessage("The password ist still missing")
                parameters[self.LOGIN_CHECKBOX].value = False
                return
            
        if (parameters[self.LOGIN_CHECKBOX].altered 
            and parameters[self.JUST_RESET].value == True):
            parameters[self.LOGIN_CHECKBOX].setErrorMessage("You have been logged out due to inactivity. Please re-login.")
            parameters[self.JUST_RESET].value = False

        # display error message if login was not successful
        if (parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].altered 
        and parameters[self.USERNAME].altered
        and parameters[self.PASSWORD].altered):
            display_msg = parameters[self.HIDDEN_LOGIN_ERROR_MESSAGE].value
            if display_msg:
                parameters[self.LOGIN_CHECKBOX].setErrorMessage(str(display_msg))
                parameters[self.LOGIN_CHECKBOX].value = False
                return

        if parameters[self.START_DATE].altered and parameters[self.START_DATE].value != None: 
            
            # get allowed start and end dates
            start_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateStart"]
            allowed_start_date = datetime.strptime(start_str, "%Y-%m-%d")
            end_str = GLOBAL_VALS["selected_factbase_data"]["attributes"]["dateEnd"]
            allowed_end_date = datetime.strptime(end_str, "%Y-%m-%d") 

            input_start = str(parameters[self.START_DATE].value)
            input_start_date = self.parse_datetime_from_string(input_start)
            if input_start_date < allowed_start_date or input_start_date > allowed_end_date:
                parameters[self.START_DATE].setErrorMessage(f"Start date is out of range.\nThe available date range for this factbase is {str(start_str)} to {str(end_str)}.\nPlease adjust the start date.")
                
        if parameters[self.END_DATE].altered and parameters[self.END_DATE].value != None:
            
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
        if parameters[self.AOI].altered and parameters[self.AOI].value != None:
 
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
        if parameters[self.FACTBASE].altered and parameters[self.FACTBASE].value != None:
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

        username = GLOBAL_VALS["preferred_username"]
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
        
        GLOBAL_VALS["inference_running"] = True

        # Inform user
        arcpy.AddMessage(f"Inference created. ID: {str(inference_id)}\n")
        arcpy.AddMessage(u"\u200B")
        arcpy.AddMessage("The request is now being processed by Sen2Cube. This process may take up to a few minutes.")
        arcpy.AddMessage("Do not terminate the tool during this time, otherwise the inference will not be loaded into the map.")
        arcpy.AddMessage(u"\u200B")

        status = "-"
        while status not in ["SUCCEEDED", "FAILED", "ABORTED"]:
            status, msg = check_inference_status(status, 
                                                 access_token=GLOBAL_VALS["access_token"], 
                                                 inference_id=inference_id)
            arcpy.AddMessage(msg)
            time.sleep(10)

        if status == "SUCCEEDED":
            get_inference_results(access_token=GLOBAL_VALS["access_token"],
                                inference_id=inference_id,
                                output_dir=output_dir)
        
        GLOBAL_VALS["inference_running"] = False


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
    
    
    def thread_to_monitor_refresh_time(self):
        """
        Monitors when the token needs to be refreshed and updates it automatically.
        """
        
        while GLOBAL_VALS["logged_in"] == True and not GLOBAL_VALS["stop_event_refresh"].is_set():

            now = datetime.now().timestamp()
            with open(TOKEN_DEBUGGING_TXT_FILE, "a") as f:
                f.write(f"\n- checking refresh time")
            
            if now >= GLOBAL_VALS["refresh_token_time"]:
            
                new_token, msg = refresh_token(token=GLOBAL_VALS["token_object"])
                if new_token:
                    with open(TOKEN_DEBUGGING_TXT_FILE, "a") as f:
                        f.write(f"\n- successfully refreshed")
                    GLOBAL_VALS['token_object'] = new_token
                    GLOBAL_VALS['access_token'] = new_token["access_token"]
                    GLOBAL_VALS['refresh_token'] = new_token["refresh_token"]
                    time_to_refresh = new_token["expires_at"] - BUFFER_SECONDS_UNTIL_TOKEN_EXPIRY
                    GLOBAL_VALS["refresh_token_time"] = time_to_refresh
            
                else:
                    GLOBAL_VALS["logged_in"] = False
                    arcpy.AddMessage(f"Could not refresh your authentication with sen2cube: {msg}.")
            
            time.sleep(5)  # Only check every 5 seconds to avoid excessive CPU use


    def start_thread_to_monitor_token_refresh_time(self):
        """Starts the token monitoring in a new thread."""
        with open(TOKEN_DEBUGGING_TXT_FILE, "a") as f:
            f.write(f"\n- Starting thread... thread refresh = {GLOBAL_VALS['thread_refresh']}")
        if GLOBAL_VALS["thread_refresh"] is None:
            GLOBAL_VALS["stop_event_refresh"].clear()  # Reset the stop event
            GLOBAL_VALS["thread_refresh"] = threading.Thread(target=self.thread_to_monitor_refresh_time)
            GLOBAL_VALS["thread_refresh"].daemon = True  # Ensures the thread stops when the main program exits
            GLOBAL_VALS["thread_refresh"].start()


    def stop_thread_to_monitor_refresh_time(self):
        """Stops the token monitoring thread."""
        with open(TOKEN_DEBUGGING_TXT_FILE, "a") as f:
            f.write(f"\n- Stopping thread")

        try:
            GLOBAL_VALS["stop_event_refresh"].set()  # Signal the thread to stop
            if GLOBAL_VALS["thread_refresh"] and GLOBAL_VALS["thread_refresh"].is_alive():
                GLOBAL_VALS["thread_refresh"].join()  # Wait for the thread to exit
        finally:
            GLOBAL_VALS["thread_refresh"] = None 
            
            with open(TOKEN_DEBUGGING_TXT_FILE, "a") as f:
                f.write(f"\n - Stopped Thread. Refresh Thread >>> {str(GLOBAL_VALS['thread_refresh'])}")


    def start_thread_to_monitor_inactivity_time(self, parameters):
        with open(DEBUGGING_TXT_FILE, "a") as f:
            f.write(f"\n- Starting thread ... thread inactivity = {GLOBAL_VALS['thread_inactivity']}")
        if GLOBAL_VALS["thread_inactivity"] is None:
            GLOBAL_VALS["stop_event_inactivity"].clear()
            GLOBAL_VALS["thread_inactivity"] = threading.Thread(target=lambda: self.thread_to_monitor_inactivity(parameters))
            GLOBAL_VALS["thread_inactivity"].daemon = True
            GLOBAL_VALS["thread_inactivity"].start()  


    def thread_to_monitor_inactivity(self, parameters):

        while GLOBAL_VALS["logged_in"] and not GLOBAL_VALS["stop_event_inactivity"].is_set():
            
            # check time, calculate inactive time
            now = datetime.now().timestamp()
            time_inactive = now - GLOBAL_VALS["last_activity_time"]
            with open(DEBUGGING_TXT_FILE, "a") as f:
                f.write(f"\n- Time inactive: {str(time_inactive)}")
            
            # if inactive for too long (and its not because there is an inference running), 
            # then start logout process
            if (time_inactive > AUTO_LOGOUT_SECONDS 
                and not GLOBAL_VALS["inference_running"]):
                
                GLOBAL_VALS["logged_in"] = False
                # the inactivity reset bool parameter is used internally 
                # to trigger the reset of parameters and to return to login page
                parameters[self.INACTIVITY_RESET].value = True

                # reset token variables
                GLOBAL_VALS["token_object"] = None
                GLOBAL_VALS["access_token"] = None
                GLOBAL_VALS["refresh_token"] = None
                GLOBAL_VALS["refresh_token_time"] = None

                with open(DEBUGGING_TXT_FILE, "a") as f:
                    f.write(f"\n- Updated the inactivity reset: {parameters[self.INACTIVITY_RESET].valueAsText}")
                break
            time.sleep(15)


    def stop_thread_to_monitor_inactivity(self):
        """Stops the inactivity thread."""
        with open(DEBUGGING_TXT_FILE, "a") as f:
            f.write(f"\n- Stopping thread")

        try:
            GLOBAL_VALS["stop_event_inactivity"].set()
            if GLOBAL_VALS["thread_inactivity"] and GLOBAL_VALS["thread_inactivity"].is_alive():
                GLOBAL_VALS["thread_inactivity"].join()
        finally:
            GLOBAL_VALS["thread_inactivity"] = None
        
            with open(DEBUGGING_TXT_FILE, "a") as f:
                f.write(f"\n - Stopped Thread. Inactivity Thread >>> {str(GLOBAL_VALS['thread_inactivity'])}")