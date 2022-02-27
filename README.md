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
Simply download the [Proof of Concept.atbx](https://github.com/Christina1281995/arcpy_toolbox_sen2cube/raw/main/Proof%20of%20Concept.atbx) and then add it to your ArcGIS Project as shown below. This toolbox was create for ArcGIS Pro 2.9.

<br>

<img src="https://user-images.githubusercontent.com/81073205/155815217-aa0b22f6-822a-4f99-a693-b838ab87f63e.png" width="80%">
<br>

When opening the toolbox, you will see the two standalone script tools. Each can be executed independently.

<img src="https://user-images.githubusercontent.com/81073205/155879690-2d4dde5e-8c3f-4b74-97ad-cb9badd81522.png" witdth="50%">

<br>
<br>

# Script Tool 1 (Static)

### **Parameters** <br>
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

<i> * Required Parameters </i>

### **Login and Session Handling** <br>
Only registered users are able to use the toolbox. Therefore, when the tool is run, a pop-up login window asks the user for credentials to request the initial session token. This token is needed to create POST and GET requests to the JSON web API that interacts with the Sen2Cube backend. The initial token is only valid for 5 minutes, thus a refreshment is performed in the backbround to keep the session alive. <br>
Major parts of logic and code for login and session handling are based on the [Sen2Cli repository](https://github.com/ZGIS/sen2cli/tree/main/sen2cli).

### **Requests** <br>
In the background, a POST request is used to post the created inference datamodel to the inference API endpoint which will then create an inference entity which is executed by the backend. When the inference is posted, the inferece status is recurrently requested using a GET request until the inference failed or was successful. In the former case the process is exited, in the latter case the outputs are accessed.

### **Output** <br>
Inference outputs can be either one or more Geotiff rasters, CSV tables or a mix of both. The outputs are read from the response object as soon as the inference status is switched to "SUCCESSFUL" by the system. The results are then downloaded into the user-specified target folder and additionally added to the active map in ArcGIS Pro. In case only CSV and no spatial information is produced, the additional AOI polygon indicates which are was investigated.

### **Additional Products** <br>
In addition to the outputs added to the map, the toolbox dynamically creates a polygon for the specified AOI and loads it together with a polygon representing the factbase coverage to the map. This is done before the tool is executed and allows the user to visually check whether the AOI lies within the factbase and identifies the AOI. The symbology was chosen in a way that the spatial information on the query is presented without being disturbing.



## Script Tool 1 (Static) Visual Concept
<!-- ![image](https://user-images.githubusercontent.com/81073205/154639979-d092f2bc-8c99-4192-b123-1166612a5ab0.png) -->

![sen2test](https://user-images.githubusercontent.com/81073205/154641356-e1387c56-3cbd-4ecb-983e-72aec67f9ea8.png)


<br>
<br>

<hr>

<br>
<br>

## Script Tool 2 (Dynamic)

The second version of the script tool implements a more dynamic functionality. <b>In contrast to the first version, which only establishes a connection with Sen2Cube when the user has already set the parameters and clicks "run", this version creates the connection to Sen2Cube at the beginning and then validates the user's parameter inputs on the fly.</b>

This tool dynamically loads information about the Sen2Cube Factbases and Knowledgebases while the user is adjusting the parameters in the GUI. Some details are listed here:
- Only factbases with the status "OK" are loaded into the drop down box for Factbases
- Once a Factbase is selected, it is shown in the map to make the Area of Interest selection more intuitive
- Once a Factbase is selected, the Factbase's valid time ranges are used to validate the user's selected dates
- Once the user selects an Area of Interest (extent), the outline is shown in the map as well



## Script Tool 2 (Dynamic) Visual Concept

<br>

![concept3 (1)](https://user-images.githubusercontent.com/81073205/155813635-031d0808-2d2f-43b1-8cf2-24d4baf76840.png)



### Time Range
This toolbox performs 3 validation checks on the user's entered time ranges. 
1. If the entered start date is either before or after the selected factbase's valid time range an Error Message is returned to the user immediately asking them to adjust this input.
2. If the entered end date is either before or after the selected factbase's valid time range an Error Message is returned to the user immediately asking them to adjust this input.
3. If the entered end date is before the entered start date an Error Message is returned to the user immediately asking them to adjust this input.

![error2](https://user-images.githubusercontent.com/81073205/155802656-2a8355ba-f91b-44c3-bbc3-ba9e05608780.png)

![error1](https://user-images.githubusercontent.com/81073205/155802258-7eb4a18a-bd47-41e8-8fdb-648593954408.png)

## Challenges and Open Issues <br>
### Challenges
A major challenge was to let the user specify the AOI extent in a way the spatial information could be transformed to input for Sen2Cube. The final implementation resulted in the user setting the current map extent as are of interest.A challenging issue thereby was handling the conversion of project extent coordinates into coordinate pairs in the right coordinate reference system so that the application could read the area of interest supplied by the user. Ultimately, this was solved by creating a function that created PointGeometries from the extent corners, which were projected into the correct reference system and returnd for accessing the suitable coordinates.
... <br>
### Open issues<br>
An open issue remains the dynamic adjusting of input parameters. While this is currently hardcoded, available fact- and knowledgebases as well as available start and end dates could be dynamically requested and offered as parameter choices. <br>
Another point is handling the specification of the AOI by the user. First the area needs checking if the size is appropriate for the system by setting a maximum valid area size. Additionally, the factbases are spatially constrained, therefore it needs to be verified that the user AOI is lies within the factbase extent.

## Future To-Do's
This list serves as reference of ideas to extend or improve the functionalities of the toolbox: <br>
- Drop-down lists for parameters (Knowledgebases, Factbases, Time Ranges) should be filled dynamically with available options requestes from the backend
  - Requires triggering the login process when accessing the parameter lists, look into the ToolValidator class in the ArcGIS Pro toolbox to custamize this behavior
  - Alternative: Using additional tkinter box (like login pop-up window), first login, then pop-up windows for knowledgebases and factbases
- When the output is a CSV file, the AOI should be converted to a polygon and added to the map as spatial reference (csv table contains no spatial information)
- Handing the user more descriptive error messages from the backend
- Transferring the logic of the entire toolbox into a QGIS Plugin using the respective plugin creator for a free software solution



## Demo Video

 https://user-images.githubusercontent.com/81073205/154838342-a6c6def6-32ff-4a1f-952a-6ccddb73af7b.mp4


