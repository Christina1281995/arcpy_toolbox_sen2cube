<img src="https://manual.sen2cube.at/img/logo_b.png" height="150px" align="center">


## Proof of Concept: An ArcGIS Pro Script Toolbox for Sen2Cube

This script tool serves as a simple proof of concept to demonstrate the compatibility of the Sen2Cube EO Data Cube with ArcGIS Pro such that registered users can access the application directly from within their ArcGIS Pro desktop software.

## Current To-Do's
- User input for Area of Interest (arcpy function to get information on CRS, then get extent in that CRS and use for AOI)
   - Validate the AOI (area size, location within given Factbase)
- Validate Time range against Factbases
- Check count and format of the outputs, and handle appropriately

## Future To-Do's
- Dynamically load the Knowledgebases and Factbases into the drop-down lists shown in the user inferface
  - Trigger the login process before showing the value list. Get factbase list and knowledgebase list -> extract names and display in drop-down list. 
  - Alternative option: Use further tkinter box (pop-up window like the login window) -> after successful login display new pop-up window with factbase and knowledgebase options.

## Concept
<!-- ![image](https://user-images.githubusercontent.com/81073205/154639979-d092f2bc-8c99-4192-b123-1166612a5ab0.png) -->

![sen2test](https://user-images.githubusercontent.com/81073205/154641356-e1387c56-3cbd-4ecb-983e-72aec67f9ea8.png)


https://github.com/Christina1281995/arcpy_toolbox_sen2cube/blob/main/src/demo_sen2cube.mp4

