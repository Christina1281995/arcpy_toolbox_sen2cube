import arcpy
import os
import json
import requests
from copy import deepcopy

INFERENCE_URL = "https://api.sen2cube.at/v1/inference"
INFERENCE_TEMPLATE = {
    "data": {
        "type": "inference",
        "attributes": {
            "owner": "-",
            "area_of_interest": "",
            "temp_range_start": "-",
            "temp_range_end": "-",
            "comment": "",
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


def get_reprojected_aoi_geojson(aoi_extent):
    '''
    Converts GPExtent (in projected CRS) to a GeoJSON polygon in EPSG:4326 (WGS84)

    Input Args:
        aoi_extent (arcpy.Extent): extent from GPExtent param

    Returns:
        str: GeoJSON polygon string with coordinates in EPSG:4326
    '''

    extent_geom = arcpy.Polygon(arcpy.Array([
        arcpy.Point(aoi_extent.XMin, aoi_extent.YMin),  # lower-left
        arcpy.Point(aoi_extent.XMax, aoi_extent.YMin),  # lower-right
        arcpy.Point(aoi_extent.XMax, aoi_extent.YMax),  # upper-right
        arcpy.Point(aoi_extent.XMin, aoi_extent.YMax),  # upper-left
        arcpy.Point(aoi_extent.XMin, aoi_extent.YMin)   # close the ring
    ]), aoi_extent.spatialReference)

    # reprject to WGS84 (EPSG:4326)
    extent_wgs84 = extent_geom.projectAs(arcpy.SpatialReference(4326))

    coords = [[pt.X, pt.Y] for pt in extent_wgs84.getPart(0)]

    geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {
                "name": "Area-of-interest 00"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }]
    }

    # returns as json string
    return json.dumps(geojson)


def send_inference(access_token: str,
                   username: str, 
                  fb_id: str, 
                  kb_id: str,
                  extent_points: str,
                  start_date: str,
                  end_date: str,
                  comment: str,
                  favorite: bool,
                  quick_preview: bool
                  ):
    """
    Fills the infrence template with all validated user inputs. 
    Sends the post request to create the infrence query. 
    
    Returns:
        (str): the inference id
    """

    inference_body = deepcopy(INFERENCE_TEMPLATE)
    inference_body["data"]["attributes"]["owner"] = username
    inference_body["data"]["relationships"]["factbase"]["data"]["id"] = fb_id
    inference_body["data"]["relationships"]["knowledgebase"]["data"]["id"] = kb_id
    coords_string = get_reprojected_aoi_geojson(extent_points)
    inference_body["data"]["attributes"]["area_of_interest"] = coords_string
    inference_body["data"]["attributes"]["temp_range_start"] = str(start_date)
    inference_body["data"]["attributes"]["temp_range_end"] = str(end_date)
    if comment != None:
        inference_body["data"]["attributes"]["comment"] = comment
    if favorite == True:
        inference_body["data"]["attributes"]["favourite"] = True
    if quick_preview == True:
        inference_body["data"]["attributes"]["output_scale_factor"] = 10

    headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}
    data = json.dumps(inference_body)

    with requests.Session() as s:
        s.headers.update(headers)
        inf_post = s.post(url=INFERENCE_URL, data=data).json()
        inference_id = inf_post.get("data", {}).get("id")

    s.close()

    return inference_id


def check_inference_status(latest_status, access_token, inference_id):
    """
    Sends get requests to check the status of an inference. 
    
    Returns:
        (str): the current status of the inference
        (str): a message to be printed to the console for the user to stay informed
    """

    headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}
    inference_endpoint = f"{INFERENCE_URL}/{str(inference_id)}"

    with requests.Session() as s:
        s.headers.update(headers)
        inference_current = s.get(inference_endpoint).json()

        status = str(inference_current["data"]["attributes"]["status"])
        if latest_status != status:
            msg =f"Current status: {str(status)}"
        if status == "FAILED":
            msg = "Inference failed."
        if status == "SUCCEEDED":
            msg = f"Inference {str(inference_id)} completed."
        else:
            msg = ""
    
    return status, msg


def get_inference_results(access_token, inference_id, output_dir):
    """
    Downloads and adds the results associated with an infrence to the map, 
    once the inference has completed.        
    """

    headers = {'Authorization': 'Bearer {}'.format(access_token), 'Content-Type': 'application/json'}
    inference_endpoint = f"{INFERENCE_URL}/{str(inference_id)}"

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

    # Inform user
    nr_of_outputs = len(output_name)
    arcpy.AddMessage(f"Number of outputs generated: {str(nr_of_outputs)}")
    arcpy.AddMessage(u"\u200B")

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
            local_file = os.path.join(str(output_dir), fname)

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
                    local_file_new = os.path.join(str(output_dir), fname_new)
                    if os.path.exists(local_file_new):
                        j = j + 1
                    else:
                        with open(local_file_new, 'wb') as f:
                            f.write(s.get(download_link, allow_redirects=True).content)
                        arcpy.AddMessage(
                            f"The output file {str(fname_new)} has been downloaded and stored at {str(output_dir)}.")
                        # Add Layer to Map
                        activeMap.addDataFromPath(local_file_new)
                        break
            else:
                local_file = os.path.join(str(output_dir), fname)
                with open(local_file, 'wb') as file:
                    file.write(s.get(download_link, allow_redirects=True).content)
                arcpy.AddMessage(f"The output file {str(fname)} has been downloaded and stored at {str(output_dir)}")
                # Adding Layer to Map
                activeMap.addDataFromPath(local_file)

        s.close()

    # Inform user
    arcpy.AddMessage('_________________')
    arcpy.AddMessage(u"\u200B")
    arcpy.AddMessage("Completed.")
    arcpy.AddMessage(u"\u200B")

    return