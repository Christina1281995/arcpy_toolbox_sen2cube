<img src="https://manual.sen2cube.at/img/logo_b.png" height="150px" align="center">


# Proof of Concept: An ArcGIS Pro Script Toolbox for Sen2Cube
This toolbox serves as a simple proof of concept to demonstrate the compatibility of the [Sen2Cube](https://www.sen2cube.at/) EO Data Cube with ArcGIS Pro such that registered users can access the application directly from within their ArcGIS Pro desktop software.
<br>
<br>
<i><b>This toolbox is a prototype. It includes two standalone script tools that represent two different versions of the Proof of Concept Script Tool. Once is a more static, light-weight tool. The second is a more dynamic tool, designed to validate parameter inputs on the fly.</b></i>
<br>
<br>

## Project Idea <br>
The idea behind this project is for a registered user to be able to access the Sen2Cube EO Data Cube directly from a desktop GIS (in this case through an ArcGIS Pro toolbox). The goal is to let the user access the application, set necessary parameters, run the query to the data cube and retrieve the information outputs directly in the GIS. This project thereby focuses on creating a first working Proof of Concept, but possible further development ideas are listed in a following section. 
A detailed description on how the semantic EO data cube and the Sen2Cube work in detail can be found in the [Manual](https://manual.sen2cube.at/index.html). <br>


## Installation in ArcGIS Pro
Simply download the [Proof of Concept.atbx](https://github.com/Christina1281995/arcpy_toolbox_sen2cube/raw/main/Proof%20of%20Concept.atbx) and then add it to your ArcGIS Project as shown below. 
Attention: This toolbox was created for <b>ArcGIS Pro Version 2.9</b>, if you are using an alternative version the toolbox may not be recognised by ArcGIS.

<br>

<img src="https://user-images.githubusercontent.com/81073205/155815217-aa0b22f6-822a-4f99-a693-b838ab87f63e.png" width="80%">
<br>

When opening the toolbox, you will see the two standalone script tools. Each can be executed independently.

<img src="https://user-images.githubusercontent.com/81073205/155879690-2d4dde5e-8c3f-4b74-97ad-cb9badd81522.png" witdth="50%">

<br>
<br>
 
# Script Tool Version 1 (Light-Weight, Static)

<i>Code file available [here](https://github.com/Christina1281995/arcpy_toolbox_sen2cube/tree/main/src/static)</i>

In this initial scipt tool the objective was to create a connection to Sen2Cube and load an inference result into the ArcGIS Pro map. The tool is structured in such a manner that all parameters are first defined by the user and when the uesr then clicks "Run" a pop up window prompts the user to login to Sen2Cube. For the login a tkinter pop-up window was created, where the user enters their credentials. This toolbox comes with a pre-defined (hard-coded) set of factbases and knowledgebases from which the user can choose. All user inputs are then converted into the required formats for the Sen2Cube inference request. Once the inference is sent, every 10 seconds the script tool checks the status of the inferece. Once the status is "Succeeded" the result is downloaded and saved in the user's specified folder and automatically loaded into the map.

A large amount of time was spent understanding the OAuth login and session handling process to correctly generate a user token and refresh it after a certain amount of time. In addition, the formatting and conversion of the data to match the Sen2Cube requirements took some trial & error. During the testing phase it was seen that the pop-up window (implemented with tkinter) appears to work differently on different devices. Since no on-the-fly parameter validation is implemented here the user must be familiar with the valid geographic and temporal ranges. 

<b>Parameters</b>

Upon opening the tool, the user is promted to set a total of 8 optional and required parameters in the toolbox user interface. While the first seven will be used for creating the inference, the last one lets the user specify an output directory for the model outputs. 
Complete list of toolbox parameters: <br>

| Nr. | Parameter | Format |
|-----|----------|------|
|  1  | Area of interest* | Extent |
|  2  | Factbase* | String (Dropdown List) |
|  3  | Knowledgebase* |String (Dropdown List) |
|  4  |Start Date* | Date |
|  5  |End Date* | Date |
|  6  |Comment | String |
|  7  |Save as Favourite in Sen2Cube Account | Boolean |
|  8  |Output Directory* | Folder |

After clicking "Run" these further parameters are required from the user in a pop-up window:


| Nr. | Parameter | Format |
|-----|----------|------|
|  9  | Username* | String |
|  10  | Password* | Hidden String |

<i> * Required Parameters </i>

<b>Login and Session Handling</b>

Only registered users are able to use the toolbox. Therefore, when the tool is run, a pop-up login window asks the user for credentials to request the initial session token. This token is needed to create POST and GET requests to the JSON web API that interacts with the Sen2Cube backend. The initial token is only valid for 5 minutes, thus a refreshment is performed in the backbround to keep the session alive. <br>
Major parts of logic and code for login and session handling are based on the [Sen2Cli repository](https://github.com/ZGIS/sen2cli/tree/main/sen2cli).

<b>Requests</b>

In the background, a POST request is used to post the created inference datamodel to the inference API endpoint which will then create an inference entity which is executed by the backend. When the inference is posted, the inferece status is recurrently requested using a GET request until the inference failed or was successful. In the former case the process is exited, in the latter case the outputs are accessed.

<b>Output</b>

Inference outputs can be either one or more Geotiff rasters, CSV tables or a mix of both. The outputs are read from the response object as soon as the inference status is switched to "SUCCESSFUL" by the system. The results are then downloaded into the user-specified target folder and additionally added to the active map in ArcGIS Pro. In case only CSV and no spatial information is produced, the additional AOI polygon indicates which are was investigated.

### How It Works

A visual step-by-step display of how the tool works. 

<!-- ![image](https://user-images.githubusercontent.com/81073205/154639979-d092f2bc-8c99-4192-b123-1166612a5ab0.png) -->

![17_concept](https://user-images.githubusercontent.com/81073205/156007240-db82b44c-bb5c-44be-be82-c2f382b9f09e.png)

<br>
<br>
<br>
<br>
<br>

# Script Tool Version 2 (Dynamic)

<i>Code Files available [here](https://github.com/Christina1281995/arcpy_toolbox_sen2cube/tree/main/src/dynamic)</i>

The second version of the script tool implements a more dynamic functionality. It is based on the first tool and implements many of the same functions. It also uses the same parameters. <b>In contrast to the first version, which only establishes a connection with Sen2Cube when the user has already set the parameters and clicks "run", this version creates the connection to Sen2Cube at the beginning and then validates the user's parameter inputs on the fly.</b>

- Only factbases with the <b>status "OK"</b> are loaded into the drop down box for Factbases
- Once a Factbase is selected, it is <b>shown in the map</b> to make the Area of Interest selection more intuitive
- Once a Factbase is selected, the Factbase's <b>valid time ranges</b> are used to validate the user's selected dates
  - If the entered start date is either before or after the selected factbase's valid time range an Error Message is returned to the user immediately asking them to adjust this input
  - If the entered end date is either before or after the selected factbase's valid time range an Error Message is returned to the user immediately asking them to adjust this input
  - If the entered end date is before the entered start date an Error Message is returned to the user immediately asking them to adjust this input
- Once the user selects an Area of Interest (extent), the outline is <b>shown in the map</b> as well
- If the Area of Interest (extent) does not <b>intersect with the Factbase's footprint</b>, an Error Message is returned to the user asking them to adjust the AOI. The error is re-evaluated if the user changes the AOI or the Factbase.

<br>

An example of these error messages is shown here:

<img src="https://user-images.githubusercontent.com/81073205/156015509-d4d3b77f-bb55-4383-a823-e5dd43eedfa6.png" width="75%">

![14_error1](https://user-images.githubusercontent.com/81073205/156014557-e08ec76b-2652-43fd-a46c-7ea24bf6684b.png)

<br>

This second version of the script tool is likely the more user-friendly Sen2Cube prototype toolbox since it actively responds to the user's input, helping the user create a successful inference request. The visual components (the AOI and the factbase footprints) also enhance the user experience. By seeing the valid factbase footprint on the map it is easier for the user to understand where to place the AOI. Though this toolbox works, there are some further issues that need to be dealt with - these are outlined in the "Challenges and Future To-Do's" below.

### How it works

A visual step-by-step display of how the tool works. 

<br>

![concept4](https://user-images.githubusercontent.com/81073205/155880565-bd09f978-2ec0-4140-9f1d-57cafa7651e3.png)



## Challenges 
<br>

<b>(1) Projections (relevant to the AOI and map outputs):</b> The default map projection in ArcGIS Pro is the Web Mercator (EPSG: 3857). This means that any given spatial extent for the AOI is, by default, passed to the script tool in the unit "meters" rather than decimal degrees or degrees-minutes-seconds. The Sen2Cube backend expects to receive the AOI in the WGS84 (EPSG: 4326) projection in decimal degrees. To resolve this the following functions were implemented:

- <i>In script tool 1</i>: The tool reads the input extent and the map's current CRS. It then converts the given extent into ARcGIS point objects and <b>reprojects</b> them from the given CRS into the WGS84 CRS. This way the map displayed in the project can stay in the CRS chosen by the user. 
- <i>In script tool 2</i>: This tool loads several intermediate objects into the map (the footprint of the factbases and the selected AOI) as well as the final results. Since the factbase footprints are in WGS84 and reprojecting them into the Web Mercator format proved difficult, this tool <b>changes the map's CRS to WGS84 </b>when the tool is opened. Upon completion the CRS of the map can, of course, be changed back into any other CRS and will still contain all of the tools output products. 

<b>(2) Scripting the Tool Validation:</b> The tool validator reacts according to the user's live parameter input. As such, no "logging" or "print messages" are available to the programmer designing the validation functions. This proved to be a tedious task. A work-around was to user a "dummy" parameter or to add Error Messages to parameters whose values contain certain messages that reveal some insight into any errors in the code. In particular, working with geographical queries or objects was complex since the input for a "dummy parameter" or for Error messages can only be a string, and converting geographical objects into useful strings was not easy (this was the case for validating if the AOI intersects the Factbase). An unresolved issue is the user input for the AOI "union of inputs" and "intersection of inputs". In both cases, no information was found about what data is sent to the script tool and in whcih format. Due to the uncertain format it was (so far) not possible to create a "dummy parameter" or an Error Message with this information. This must be handled in the future.

## Future To-Do's
- Allowing a more diverse input for the AOI. Currently the tool only accepts an extent. In the future, this should be expanded for more complex shapes.
- The default option of the AOI needs to be handled.
- Implement an area check on the entered AOI, i.e. with a maximum allowed size to avoid a user time-out after 600 seconds.
- Handing the user more descriptive error messages from the backend.
- Transferring the logic of the entire toolbox into a QGIS Plugin using the respective plugin creator for a free software solution.
- Handle "Union of Inputs" and "Intersection of Inputs" for the AOI options. It's unclear what data and which format is passed to the script tool.
- Add metadata! Not possible while creating the toolbox: 

![15_metadata](https://user-images.githubusercontent.com/81073205/156004080-8b7fbd80-a090-4cf3-8c13-d76e2bb60300.png)


## Contributions

<b>Niklas Jaggy</b> - Login and Session Handling, POST requests to Sen2Cube, GET requests to Sen2Cube, filling inference request based on user input, displaying AOI in map, JSON data formatting, extracting information from inference result, documentation, general toolbox development, AOI area size validation (in progress)

<b>Christina Zorenboehmer</b> - Login and Session Handling, token refresh, Pop-Up login box, AOI CRS reprojection, filling inference request based on user input, JSON data formatting, handling multiple inference outputs and loading into map, validation functions for dynamic script tool (loading factbases and knowledgebases into parameters after login, validating time ranges and AOI on the fly, loading factbase AOIs into map on the fly, validation class login handling), general toolbox development, documentation

## Demo Video 

Kabul River, Afghanistan: Count Water Presence Inference.

This demo shows an example of how to use the toolbox and then work with the results in ArcGIS.

<img src="https://user-images.githubusercontent.com/81073205/157129666-bd5048a5-7156-44a1-aad5-3bcba14b686a.gif" width="30%">

### Demo (1/2): Downloading Toolbox, Parameterisation

https://user-images.githubusercontent.com/81073205/157130738-7008e2ec-e4fb-4dfd-8c7c-ecd721c8f38e.mp4

### Demo (2/2): Visualising Results

https://user-images.githubusercontent.com/81073205/157130825-08cd7dd9-79a2-4177-8078-7d9db24695d1.mp4

