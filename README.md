<img src="https://manual.sen2cube.at/img/logo_b.png" height="150px" align="center">


## Proof of Concept: An ArcGIS Pro Script Toolbox for Sen2Cube

This script tool serves as a simple proof of concept to demonstrate the compatibility of the [Sen2Cube](https://www.sen2cube.at/) EO Data Cube with ArcGIS Pro such that registered users can access the application directly from within their ArcGIS Pro desktop software.

## Current To-Do's
- Check refresh token
  - Current code refreshes token after 200 seconds --> worked once, failed once. More investagations needed about how refresh token is handled
- Get error message if status == "failed"
- Validate the AOI (area size, location within given Factbase)
- Validate Time range against Factbases
- Lots of Testing
- Check other Factbases (Afghanistan and Syria) and make sure they work as well
- Add metadata documentation to toolbox

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

