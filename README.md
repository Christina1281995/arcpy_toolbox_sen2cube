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
Only registered users are able to use the toolbox. Therefore, when running the tool, a pop-up login window fetches the user credentials to request the initial session token. This token is needed to create POST and GET requests to the JSON web API that interacts with the Sen2Cube backend. The initial token is only valid for 5 minutes, thus a refreshment is performed in the backbround to keep the session alive. 

### **Parameters** <br>
The user can and partly must set a total of 8 parameters in the toolbox UI. While the first seven will be used for creating the inference, the last one lets the user specify an output directory for the model outputs. 
Complete list of toolbox parameters: <br>

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
Inference outputs can be either one or more Geotiff rasters, CSV tables or a mix of both. The outputs ar eread from the response object as soon as the inference status is switched to "SUCCESSFUL" by the system. The results are then downloaded into the user-specified target folder and additionally added to the active map in ArcGIS Pro.

_-----New----_ <br>
## Challenges and Open Issues <br>
A challenging issue was handling the conversion of project extent coordinates into coordinate pairs in the right coordinate reference system so that the application could read the area of interest supplied by the user. 
... <br>
### Open issues### <br>
An open issue remains the dynamic adjusting of input parameters. While this is currently hardcoded, available fact- and knowledgebases as well as available start and end dates could be dynamically requested and offered as parameter choices. <br>
Another point is handling the specification of the AOI by the user. First the area needs checking if the size is appropriate for the system by setting a maximum valid area size. Additionally, the factbases are spatially constrained, therefore it needs to be verified that the user AOI is lies within the factbase extent.

_-----New----_

## Future To-Do's
- Dynamically load the Knowledgebases, Factbases, and Time Ranges into the drop-down lists shown in the user inferface
  - Trigger the login process before showing the value list. Get factbase list and knowledgebase list -> extract names and display in drop-down list. 
  - Alternative option: Use further tkinter box (pop-up window like the login window) -> after successful login display new pop-up window with factbase and knowledgebase options.
- If output is "csv", add an AOI shapefile to the map as well (csv table contains no spatial information)

## Step-By-Step
<!-- ![image](https://user-images.githubusercontent.com/81073205/154639979-d092f2bc-8c99-4192-b123-1166612a5ab0.png) -->

![sen2test](https://user-images.githubusercontent.com/81073205/154641356-e1387c56-3cbd-4ecb-983e-72aec67f9ea8.png)


## Demo Video

https://user-images.githubusercontent.com/81073205/154838342-a6c6def6-32ff-4a1f-952a-6ccddb73af7b.mp4

