<img src="https://manual.sen2cube.at/img/logo_b.png" height="150px" align="center">


# Proof of Concept: An ArcGIS Pro Script Toolbox for Sen2Cube
This script tool serves as a simple proof of concept to demonstrate the compatibility of the [Sen2Cube](https://www.sen2cube.at/) EO Data Cube with ArcGIS Pro such that registered users can access the application directly from within their ArcGIS Pro desktop software.

_-----New----_ <br>
## Project Idea <br>
The idea behind this project is for a registered user to be able to access the Sen2Cube EO Data Cube directly from a desktop GIS via a plugin (QGIS) or a toolbox (ArcGIS Pro). For this project the toolbox version was chosen. The goal is to let the user access the application, set necessary parameters, run the query to the data cube and retrieve the information outputs directly in the GIS. This project thereby focuses on creating a first working Proof of Concept, but possible further development ideas are listed in a following section. 
A detailed description on how the semantic EO data cube and the Sen2Cube work in detail can be found in the [Manual](https://manual.sen2cube.at/index.html). <br>
_-----New----_

_-----New----_ <br>
## Implementation <br>
### **Login and Session Handling** <br>
As only registered users should be able to use the toolbox, a pop-up login window was created to fetch the user credentials with which the first session token was requested. This token is necessary to post and get requests to and from the application backend. Because the initial token is only valid for 5 minutes, it needs to be refreshed in time to keep the session alive.

### **Parameters** <br>
- taken from toolbox UI
- majority inserted into the inferece datamodel 
- AOI checked for size limits and added as layer to map

| Parameter | Format |
|----------|------|
| Area of interest | Extent |
| Factbase | String (Dropdown List) |
| Knowledgebase |String (Dropdown List) |
| Start Date | Date |
| End Date | Date |
| Comment | String |
| Favorite? | Boolean |
| Output Directory | Folder |

### **Requests** <br>


### **Output**
Outputs are read from the reponse after an inference has run successfully. These outputs, geotiff rasters or CSV tables, are then accessed and downloaded via a link, stored locally in the directory specified by the user and added to the current active map for direct inspection.


_-----New----_ <br>
## Challenges and Open Issues <br>
A challenging issue was handling the conversion of project extent coordinates into coordinate pairs in the right coordinate reference system so that the application could read the area of interest supplied by the user. 
...
An open issue remains the dynamic adjusting of input parameters. While this is currently hardcoded, available fact- and knowledgebases as well as available start and end dates could be dynamically requested and offered as parameter choices. 

_-----New----_

## Future To-Do's
- Dynamically load the Knowledgebases, Factbases, and Time Ranges into the drop-down lists shown in the user inferface
  - Trigger the login process before showing the value list. Get factbase list and knowledgebase list -> extract names and display in drop-down list. 
  - Alternative option: Use further tkinter box (pop-up window like the login window) -> after successful login display new pop-up window with factbase and knowledgebase options.
- If output is "csv", add an AOI shapefile to the map as well (csv table contains no spatial information)

## Concept
<!-- ![image](https://user-images.githubusercontent.com/81073205/154639979-d092f2bc-8c99-4192-b123-1166612a5ab0.png) -->

![sen2test](https://user-images.githubusercontent.com/81073205/154641356-e1387c56-3cbd-4ecb-983e-72aec67f9ea8.png)


## Demo Video

https://user-images.githubusercontent.com/81073205/154838342-a6c6def6-32ff-4a1f-952a-6ccddb73af7b.mp4

