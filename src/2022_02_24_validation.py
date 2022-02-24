import arcpy
import os

class ToolValidator:
  # Class to add custom behavior and properties to the tool and tool parameters.

    def __init__(self):
        # set self.params for use in other function
        self.params = arcpy.GetParameterInfo()

    def initializeParameters(self):
        # Customize parameter properties. 
        # This gets called when the tool is opened.
        return

    def updateParameters(self):
        # Modify parameter values and properties.
        # This gets called each time a parameter is modified, before 
        # standard validation.

        db_path = arcpy.mp.ArcGISProject("CURRENT").defaultGeodatabase
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        activeMap = arcpy.mp.ArcGISProject("CURRENT").activeMap
        map_spatial_reference = activeMap.spatialReference.PCSCode
        spatial_reference = arcpy.SpatialReference(map_spatial_reference)

        filename_austria = "BoundingBox_Sen2Cube_Austria"
        filename_afghanistan = "BoundingBox_Sen2Cube_Afghanistan"
        filename_syria = "BoundingBox_Sen2Cube_Syria"

        layer_austria = os.path.join(str(db_path), filename_austria)
        layer_afghanistan = os.path.join(str(db_path), filename_afghanistan)
        layer_syria = os.path.join(str(db_path), filename_syria)


        # AUSTRIA BBOX
        if self.params[0].value == "1 - Austria" and not arcpy.Exists(layer_austria):
            # if a syrian layer already exists
            if not arcpy.Exists(layer_austria):
                if arcpy.Exists(layer_syria):
                    arcpy.Delete_management(layer_syria)   
                elif arcpy.Exists(layer_afghanistan):
                    arcpy.Delete_management(layer_afghanistan)

                # Create a factbase bounding box geometry
                bbox_array = arcpy.Array([arcpy.Point(16.94618, 48.61907),
                    arcpy.Point(16.84472, 48.36197),
                    arcpy.Point(17.16639, 48.0125),
                    arcpy.Point(17.05389, 47.70944),
                    arcpy.Point(16.45055, 47.69805),
                    arcpy.Point(16.71389, 47.54388),
                    arcpy.Point(16.45201, 47.41284),
                    arcpy.Point(16.50486, 47.00677),
                    arcpy.Point(15.85903, 46.72319),
                    arcpy.Point(14.8675, 46.61333),
                    arcpy.Point(14.545, 46.4075),
                    arcpy.Point(12.44055, 46.69083),
                    arcpy.Point(12.16028, 46.92806),
                    arcpy.Point(12.18611, 47.09458),
                    arcpy.Point(11.17715, 46.96736),
                    arcpy.Point(11.0168, 46.77333),
                    arcpy.Point(10.49778, 46.85527),
                    arcpy.Point(10.39076, 47.00257),
                    arcpy.Point(10.10944, 46.85027),
                    arcpy.Point(9.59863, 47.06384),
                    arcpy.Point(9.53357, 47.27454),
                    arcpy.Point(9.67035, 47.39069),
                    arcpy.Point(9.56672, 47.54045),
                    arcpy.Point(9.81097, 47.59416),
                    arcpy.Point(10.23174, 47.37374),
                    arcpy.Point(10.17333, 47.27472),
                    arcpy.Point(10.4818, 47.58652),
                    arcpy.Point(11.10403, 47.39652),
                    arcpy.Point(12.73694, 47.6827),
                    arcpy.Point(13.0125, 47.46979),
                    arcpy.Point(13.10014, 47.64292),
                    arcpy.Point(12.91396, 47.725),
                    arcpy.Point(13.00889, 47.85416),
                    arcpy.Point(12.75972, 48.12173),
                    arcpy.Point(13.395, 48.3661),
                    arcpy.Point(13.44323, 48.56024),
                    arcpy.Point(13.726, 48.51558),
                    arcpy.Point(13.83361, 48.77361),
                    arcpy.Point(14.70028, 48.58138),
                    arcpy.Point(15.02861, 49.01875),
                    arcpy.Point(16.10333, 48.75),
                    arcpy.Point(16.54055, 48.81236),
                    arcpy.Point(16.94618, 48.61907)
                ])
                
                bbox = arcpy.Polygon(bbox_array, spatial_reference=4326)
                bbox_proj =  bbox.projectAs(arcpy.SpatialReference(3857))
                arcpy.CreateFeatureclass_management(db_path, filename_austria, "POLYGON", spatial_reference = arcpy.SpatialReference(3857))
                # Open an InsertCursor and insert the new geometry
                cursor = arcpy.da.InsertCursor(layer_austria, ['SHAPE@'])
                cursor.insertRow([bbox])
                # Delete cursor object
                del cursor
                
                activeMap.addDataFromPath(layer_austria)

                layers = activeMap.listLayers()
                for layer in layers:
                    if layer.name == "BoundingBox_Sen2Cube_Austria":
                        if layer.supports("TRANSPARENCY"):
                            layer.transparency = 60
            
        # AFGHANISTAN BBOX
        elif self.params[0].value == "2 - Afghanistan" and not arcpy.Exists(layer_afghanistan):
            # if a syrian layer already exists
            if not arcpy.Exists(layer_afghanistan):
                if arcpy.Exists(layer_austria):
                    arcpy.Delete_management(layer_austria)   
                elif arcpy.Exists(layer_syria):
                    arcpy.Delete_management(layer_syria)

                # Create a factbase bounding box geometry
                bbox_array = arcpy.Array([arcpy.Point(68.99978017400008, 35.24307771200006),
                arcpy.Point(70.20650672500005, 35.23706389000006),
                arcpy.Point(70.19219818900007, 34.247124376000045),
                arcpy.Point(68.99978278200007, 34.25292158800005),
                arcpy.Point(68.99978017400008, 35.24307771200006)
                ])

                bbox = arcpy.Polygon(bbox_array, spatial_reference)
                # bbox_proj =  bbox.projectAs(arcpy.SpatialReference(4326))
                arcpy.CreateFeatureclass_management(db_path, filename_afghanistan, "POLYGON", spatial_reference = arcpy.SpatialReference(spatial_reference))
                # Open an InsertCursor and insert the new geometry
                cursor = arcpy.da.InsertCursor(layer_afghanistan, ['SHAPE@'])
                cursor.insertRow([bbox])
                # Delete cursor object
                del cursor

                activeMap.addDataFromPath(layer_afghanistan)

                layers = activeMap.listLayers()
                for layer in layers:
                    if layer.name == "BoundingBox_Sen2Cube_Afghanistan":
                        if layer.supports("TRANSPARENCY"):
                            layer.transparency = 60
                
        # SYRIA BBOX 
        elif self.params[0].value == "3 - Syria" and not arcpy.Exists(layer_syria):
            # if a syrian layer already exists
            if not arcpy.Exists(layer_syria):
                if arcpy.Exists(layer_austria):
                    arcpy.Delete_management(layer_austria)   
                elif arcpy.Exists(layer_afghanistan):
                    arcpy.Delete_management(layer_afghanistan)

                # Create a factbase bounding box geometry
                bbox_array = arcpy.Array([arcpy.Point(36.90980180694326, 35.22502656204854),
                arcpy.Point(36.9098528279, 35.2250276976),
                arcpy.Point(36.91097310558689, 35.180281695198936),
                arcpy.Point(36.9121087583, 35.1368985412),
                arcpy.Point(36.912059289995554, 35.136897442591575),
                arcpy.Point(36.9346264729, 34.235521621),
                arcpy.Point(35.7438223364, 34.2096670331),
                arcpy.Point(35.706580264723215, 35.1535068498808),
                arcpy.Point(35.66943791443368, 36.05381348944793),
                arcpy.Point(35.6286817908, 36.9986680798),
                arcpy.Point(36.75163506714068, 37.0247555263675),
                arcpy.Point(36.7516200961, 37.0252757852),
                arcpy.Point(36.806543580234106, 37.026031111854095),
                arcpy.Point(36.8614943754, 37.0273076796),
                arcpy.Point(36.86150862641083, 37.02678701008371),
                arcpy.Point(37.87507228168083, 37.04072588625876),
                arcpy.Point(37.8750647374, 37.0412497841),
                arcpy.Point(37.9303744008437, 37.041486420032065),
                arcpy.Point(37.9856974615, 37.0422472418),
                arcpy.Point(37.98570426652832, 37.04172314239706),
                arcpy.Point(39.1097593208, 37.0465322806),
                arcpy.Point(39.1083684575, 36.0566749851),
                arcpy.Point(37.94392522330954, 36.05180700627501),
                arcpy.Point(36.8885301955395, 36.037624975877286),
                arcpy.Point(36.90980180694326, 35.22502656204854)
                ])
                
                bbox = arcpy.Polygon(bbox_array, spatial_reference)
                # bbox_proj =  bbox.projectAs(arcpy.SpatialReference(4326))
                arcpy.CreateFeatureclass_management(db_path, filename_syria, "POLYGON", spatial_reference = arcpy.SpatialReference(spatial_reference))
                # Open an InsertCursor and insert the new geometry
                cursor = arcpy.da.InsertCursor(layer_syria, ['SHAPE@'])
                cursor.insertRow([bbox])
                # Delete cursor object
                del cursor
                
                activeMap.addDataFromPath(layer_syria)

                layers = activeMap.listLayers()
                for layer in layers:
                    if layer.name == "BoundingBox_Sen2Cube_Syria":
                        if layer.supports("TRANSPARENCY"):
                            layer.transparency = 60
                

        # SHOW AOI IN MAP
        if self.params[2].altered:
            filename = "Your_AOI"
            layer_path= os.path.join(str(db_path), filename)
            
            if arcpy.Exists(layer_path):
                pass
            else:
                activeMap = arcpy.mp.ArcGISProject("CURRENT").activeMap
        
                #  new empty arrays for points
                points1 = []
    
                individual_units = str(self.params[2].value).split()
                for i in range(4):
                    points1.append(individual_units[i].replace(",", "."))   
                polyArray = arcpy.Array()
                for i in range(4):
                    polyArray.add(arcpy.Point(float(points1[0]), float(points1[1])))
                    polyArray.add(arcpy.Point(float(points1[2]), float(points1[1])))
                    polyArray.add(arcpy.Point(float(points1[2]), float(points1[3])))
                    polyArray.add(arcpy.Point(float(points1[0]), float(points1[3])))
                    polyArray.add(arcpy.Point(float(points1[0]), float(points1[1])))
                
                poly = arcpy.Polygon(polyArray, spatial_reference)
                # poly_proj =  poly.projectAs(map_spatial_reference))
                arcpy.CreateFeatureclass_management(db_path, filename, "POLYGON", spatial_reference = arcpy.SpatialReference(spatial_reference))
                cur = arcpy.da.InsertCursor(layer_path, "SHAPE@")
                cur.insertRow([poly])
                del cur
                activeMap.addDataFromPath(layer_path)

                layers = activeMap.listLayers()
                for layer in layers:
                    if layer.name == "Your_AOI":
                        sym = layer.symbology
                        sym.renderer.symbol.color = {'RGB': [0, 0, 0, 100]}
                        sym.renderer.symbol.outlineColor = {'RGB': [0, 0, 0, 0]}

        return

    def updateMessages(self):
        # Customize messages for the parameters.
        # This gets called after standard validation.
        return

    # def isLicensed(self):
    #     # set tool isLicensed.
    # return True
