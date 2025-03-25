import arcpy

MAX_ALLOWED_SIZE_OF_AOI = "TBD"

def validate_aoi(extent, fb_geojson_geometry, fb_srs):
    """
    Converts user input extent to Arcpy Polygon,
    Loads the factbase footprint, 
    Performs various checks to see if the two geometries 
    overlap in any way. 

    Inputs:
        extent (GPExtent): the user's input 
        fb_geojson_geometry (str): the coordinates for the factbase geometry
    
    Returns;
        (bool): True if the user extent and the factbase footprint overlap
    """

    xmin, ymin, xmax, ymax = extent.XMin, extent.YMin, extent.XMax, extent.YMax
    extent_geom = arcpy.Polygon(arcpy.Array([
        arcpy.Point(xmin, ymin),
        arcpy.Point(xmin, ymax),
        arcpy.Point(xmax, ymax),
        arcpy.Point(xmax, ymin),
        arcpy.Point(xmin, ymin)  # close ring
    ]), extent.spatialReference)

    geom_type = fb_geojson_geometry['type']
    coords = fb_geojson_geometry['coordinates']

    if geom_type.lower() == "multipolygon":
        geometries = []

        for polygon in coords:
            part_array = arcpy.Array()
            for ring in polygon:
                ring_array = arcpy.Array()
                for pt in ring:
                    x, y = pt[:2]  # ignore Z
                    ring_array.add(arcpy.Point(x, y))
                part_array.add(ring_array)
            poly = arcpy.Polygon(part_array, arcpy.SpatialReference(4326))
            geometries.append(poly)

        footprint_geom = geometries[0]
        for g in geometries[1:]:
            footprint_geom = footprint_geom.union(g)

    elif geom_type.lower() == "polygon":
        part_array = arcpy.Array()
        for ring in coords: 
            ring_array = arcpy.Array()
            for pt in ring:
                x, y = pt[:2]  # ignore Z
                ring_array.add(arcpy.Point(x, y))
            part_array.add(ring_array)
        footprint_geom = arcpy.Polygon(part_array, arcpy.SpatialReference(4326))

    # project to match the extent's spatial reference
    if footprint_geom.spatialReference.factoryCode != extent.spatialReference.factoryCode:
        footprint_geom = footprint_geom.projectAs(extent.spatialReference)

    if extent_geom.overlaps(footprint_geom): 
        return True
    elif extent_geom.intersect(footprint_geom, dimension=2):
        return True
    elif extent_geom.contains(footprint_geom):
        return True
    elif extent_geom.within(footprint_geom):
        return True
    else:
        return False

