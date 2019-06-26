# 3D Network Toolbox for ArcGIS 10.x
    # Christopher D. Higgins
    # Jimmy Chan
    # Department of Land Surveying and Geo-Informatics
    # The Hong Kong Polytechnic University
    
import os
import arcpy
import osmnx as ox
import json
import sys
from datetime import datetime
import traceback

# parameters hardcoded
query_no_slope = "TUNNEL = 'yes' Or BRIDGE = 'yes'"
search_radius = 0.001
extension_list = ["3D", "Spatial"]
date_time_obj = datetime.now()
timestamp = date_time_obj.strftime("%H%M%S")

# parameters provided by user
param_in_dtm = None
param_in_network = None
param_sample_distance = None
param_has_no_split_edges = None
param_has_no_slope_edges = None
param_out_network_dir = None
param_location_save_name = None

# temporary file names
lyr_lines_split = 'in_memory\\lyr_lines_split'
lyr_points_split = 'in_memory\\lyr_points_split'
lyr_interpolated_lines = 'in_memory\\lyr_interpolated_lines'
lyr_lines_nosplit = 'in_memory\\lyr_lines_nosplit'
lyr_lines_nosplit_3d = 'in_memory\\lyr_lines_nosplit_3d'
lyr_lines_interpolate_select = 'in_memory\\lyr_lines_interpolate_select'
lyr_output_feature_class_select = 'in_memory\\lyr_output_feature_class_select'
lyr_output_feature_class = 'in_memory\\lyr_output_feature_class'
lyr_dissolved_lines = 'in_memory\\lyr_dissolved_lines'
lyr_lines_select = 'in_memory\\lyr_lines_select'

# operation names of 3d/4d fields
add_field_Z = "ADD_FIELD_Z"
calculate_field_z = "CALCULATE_FIELD_Z"
add_walktime_field = "ADD_WALKTIME_FIELD"
calculate_walktime_field = "CALCULATE_WALKTMIE_FIELD"
add_circle_segment = "ADD_CIRCLE_SEGMENT"
calculate_circle_segment = "CALCULATE_CIRCLE_SEGMENT"


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "3D Network Toolbox"
        self.alias = "Network3D"

        # List of tool classes associated with this toolbox
        self.tools = [MainNetwork2DTo3D, CollectDataFromOsm, NetworkInterpolation, DtmRename]


class MainNetwork2DTo3D(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Full OSM Network Extraction and Interpolation"
        self.description = "Extracts data from OSM and interpolates the 2D networks into 3D using Digital Terrain Models"
        self.canRunInBackground = True
        self.category = "3D Network"

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Cities JSON File",
            name="Input_JSON",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ['json']

        param1 = arcpy.Parameter(
            displayName="New OSM Cities Output Folder",
            name="New_OSM_Cities_Output_folder",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Output")

        param2 = arcpy.Parameter(
            displayName="Input DTM Folder",
            name="Input_DTM_Folder",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input")

        param3 = arcpy.Parameter(
            displayName="Sample Distance",
            name="Distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param3.filter.type = "Range"
        param3.filter.list = [1.0,  float("inf")]
        param3.defaultEnvironmentName = 10.0
        param3.value = 10.0

        param4 = arcpy.Parameter(
            displayName="Network has No Split edges",
            name="FalseSplit",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param4.value = False
        
        param5 = arcpy.Parameter(
            displayName="Network has No Slope edges",
            name="FalseSlope",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param5.value = False

        param6 = arcpy.Parameter(
            displayName="New 3D Network Output Folder",
            name="New_3D_Network_Output_Folder",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("3D") != "Available" or arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
                return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, message):
        self.run_main_workflow(parameters)

    def run_main_workflow(self, params):
        arcpy.AddMessage("== Run tool ==")
        try:
            param_cities_json = params[0].valueAsText
            param_osm_shp_folder = params[1].valueAsText + "/data"

            cities_list_json = read_cities_list(param_cities_json)
            collect_data(cities_list_json, param_osm_shp_folder)

            arcpy.AddMessage("== Tool Run Complete ==")
        except Exception as e:
            arcpy.AddMessage("*****" + str(e) + "*****")
            arcpy.AddMessage(traceback.print_tb(e.__traceback__))


class CollectDataFromOsm(object):

    param_cities_json = None
    param_folder_path = None

    def __init__(self):
        self.label = "Extract Data from OSM"
        self.description = "Extract OSM 2D network based on input JSON file"
        self.canRunInBackground = True
        self.category = "3D Network"

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input JSON File",
            name="Input_JSON",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        param0.filter.list = ['json']

        param1 = arcpy.Parameter(
            displayName="New OSM Cities Output Folder",
            name="New_OSM_Cities_Output_folder",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Output")

        params = [param0, param1]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("3D") != "Available" or arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        self.download_data(parameters)


    def download_data(self, params):
        try:
            # Could be called from outside
            # Main workflow for downloading data
            global param_cities_json, param_folder_path
            param_cities_json = params[0].valueAsText
            # Creates a subfolder named "data"
            param_folder_path = params[1].valueAsText

            cities_list_json = read_cities_list(param_cities_json)
            collect_data(cities_list_json, param_folder_path)
        except Exception as e:
            arcpy.AddMessage("*****" + str(e) + "*****")
            arcpy.AddMessage(traceback.print_tb(e.__traceback__))


class NetworkInterpolation(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Network Interpolation"
        self.description = "Interpolate 3D Network from 2D Network using Digital Terrain Model"
        self.canRunInBackground = True
        self.category = "3D Network"

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Network (2D)",
            name="Input_Line_Feature_Class",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="Input Surface",
            name="Input_Surface",
            datatype=["GPLayer", "DERasterDataset", "GPFeatureLayer"],
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="Sample Distance",
            name="Distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")

        param2.filter.type = "Range"
        param2.filter.list = [1.0, float("inf")]
        param2.defaultEnvironmentName = 10.0
        param2.value = 10.0

        param3 = arcpy.Parameter(
            displayName="Network has No Split edges",
            name="FalseSplit",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param3.value = False

        param4 = arcpy.Parameter(
            displayName="Network has No Slope edges",
            name="FalseSlope",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        param4.value = False

        param5 = arcpy.Parameter(
            displayName="Output Network (3D)",
            name="Network_3D_3",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Output")

        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        try:
            if arcpy.CheckExtension("3D") != "Available" or arcpy.CheckExtension("Spatial") != "Available":
                raise Exception
        except Exception:
            return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, message):
        self.interpolate(parameters, True)

    def get_current_timestamp_str(self):
        date_time = datetime.now()
        return date_time.strftime("%m/%d/%Y %H:%M:%S")

    def set_interpolation_params(self, params, standalone=False):
        # Retrieve user entered parameters
        global param_in_dtm, param_in_network, param_sample_distance, param_has_no_split_edges, param_has_no_slope_edges, param_out_network_dir, param_location_save_name, param_out_gdb, param_out_network
        if params is None:
            params = sys.argv

        if standalone:
            param_in_network = params[0].valueAsText
            param_in_dtm = params[1].valueAsText
            param_sample_distance = params[2].valueAsText
            param_has_no_split_edges = params[3].value
            param_has_no_slope_edges = params[4].value
            #param_out_network_dir = params[5] + "_" + timestamp
            param_out_network_dir = "{0}/output/network".format(params[5].valueAsText)
            param_out_gdb = "{0}_{1}.gdb".format(param_location_save_name, timestamp)
            param_out_network = param_out_network_dir + "/" + param_out_gdb + "/network"
        else:
            param_location_save_name = params[6].valueAsText
            param_in_network = "{0}/data/osm_{1}/edges/edges.shp".format(params[0].valueAsText, param_location_save_name)
            param_in_dtm = "{0}/{1}".format(params[1].valueAsText, param_location_save_name + ".tif")
            param_sample_distance = params[2].valueAsText
            param_has_no_split_edges = params[3].value
            param_has_no_slope_edges = params[4].value
            param_out_network_dir = "{0}/output/network".format(params[5].valueAsText)
            param_out_gdb = "{0}.gdb".format(param_location_save_name)
            param_out_network = param_out_network_dir + "/" + param_out_gdb + "/network"

        #Parameters for testing only

        '''
        param_in_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "OSMnx_Walk"
        param_in_dtm = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "HK_DTM_2m_Clip"
        param_sample_distance = float('10')
        param_has_no_split = True
        param_has_no_slope = True
        param_out_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Test.gdb/testoutput_{0}".format(timestamp)
        '''


    def check_out_extension(self):
        for extension in extension_list:
            arcpy.CheckOutExtension(extension)
        return


    def check_in_extension(self):
        for extension in extension_list:
            arcpy.CheckInExtension(extension)
        return


    def delete_in_memory(self):
        # Delete in-memory table
        arcpy.Delete_management("in_memory\\{0}".format(timestamp))
        return


    def generate_points_along_lines(self, lines_layer):
        try:
            arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE",
                                                      float(param_sample_distance), "", "")
        except ValueError:
            arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE", 10, "", "")


    def add_fields_or_calculate(self, case, param_lyr=None):
        if case == add_field_Z:
            arcpy.AddFields_management(param_lyr,
                                       "Start_Z DOUBLE # # # #;"
                                       "End_Z DOUBLE # # # #;"
                                       "Max_Z DOUBLE # # # #;"
                                       "Start_X DOUBLE # # # #;"
                                       "Start_Y DOUBLE # # # #;"
                                       "End_X DOUBLE # # # #;"
                                       "End_Y DOUBLE # # # #;"
                                       )
            return
        elif case == calculate_field_z:
            arcpy.CalculateGeometryAttributes_management(param_lyr, "Start_X LINE_START_X;Start_Y LINE_START_Y;End_X LINE_END_X;End_Y LINE_END_Y;Start_Z LINE_START_Z;End_Z LINE_END_Z", None, None, None)
            arcpy.CalculateFields_management(param_lyr,
                                             "PYTHON3",
                                             "Max_Z 'max(!Start_Z!, !End_Z!)';",
                                             None)
            return
        elif case == add_walktime_field:
            arcpy.AddFields_management(param_lyr,
                                       "FT_MIN_2D DOUBLE # # # #;"
                                       "TF_MIN_2D DOUBLE # # # #;"
                                       "FT_MIN_3D DOUBLE # # # #;"
                                       "TF_MIN_3D DOUBLE # # # #;"
                                       )
            return
        elif case == calculate_walktime_field:
            arcpy.CalculateFields_management(param_lyr,
                                             "PYTHON3",
                                             "FT_MIN_2D (!shape.length!/(5036.742125))*60;"
                                             "TF_MIN_2D (!shape.length!/(5036.742125))*60;"
                                             "FT_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*1000))*60;"
                                             "TF_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*1000))*60;",
                                             None)
            return
        elif case == add_circle_segment:
            arcpy.AddFields_management(param_lyr,
                                       "SEGMENT_ID LONG # # # #;"
                                       )

            return
        elif case == calculate_circle_segment:
            arcpy.SelectLayerByAttribute_management(param_lyr, "NEW_SELECTION", "Start_X = End_X And Start_Y = End_Y", None)
            if len(arcpy.ListFields(param_lyr, "OBJECTID")) > 0:
                arcpy.CalculateField_management(param_lyr, "SEGMENT_ID", "!OBJECTID!", "PYTHON3", None)
            else:
                arcpy.CalculateField_management(param_lyr, "SEGMENT_ID", "!FID!", "PYTHON3", None)
            arcpy.SelectLayerByAttribute_management(param_lyr, "CLEAR_SELECTION")

        return


    def replace_no_slope_edges(self):
        if param_has_no_slope_edges:
            arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "NEW_SELECTION", query_no_slope)
            arcpy.CalculateFields_management(lyr_output_feature_class_select, "PYTHON3", "FT_MIN_3D !FT_MIN_2D!;TF_MIN_3D !TF_MIN_2D!", None)


    def calculate_3d_attributes(self, lines_layer):

        # Add SEGMENT_ID to circular lines
        arcpy.MakeFeatureLayer_management(lines_layer, lyr_lines_select)
        self.add_fields_or_calculate(add_circle_segment, lyr_lines_select)
        self.add_fields_or_calculate(calculate_circle_segment, lyr_lines_select)

        # Generate Points Along Lines
        self.generate_points_along_lines(lyr_lines_select)

        # Split Lines at Points
        arcpy.SplitLineAtPoint_management(lyr_lines_select, lyr_points_split, lyr_output_feature_class, search_radius)
        self.add_fields_or_calculate(calculate_field_z, lyr_output_feature_class)

        # Add Z Information
        arcpy.AddZInformation_3d(lyr_output_feature_class, "LENGTH_3D;AVG_SLOPE", "NO_FILTER")

        # Add walk time fields
        self.add_fields_or_calculate(add_walktime_field, lyr_output_feature_class)

        # Calculate walk time fields
        self.add_fields_or_calculate(calculate_walktime_field, lyr_output_feature_class)

        # MakeFeatureLayer - temp output_feature_class_lyr
        arcpy.MakeFeatureLayer_management(lyr_output_feature_class, lyr_output_feature_class_select)

        # Replace 3D walk time with 2D walk time for any No_Slope lines
        self.replace_no_slope_edges()
        return


    def simplify_and_generate_output(self):

        # Copy lines with slope to output layer -- avoid circular segments (those with SEGMENT_ID)
        arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "NEW_SELECTION", "AVG_SLOPE = 0 OR SEGMENT_ID is not null")
        if not os.path.exists(param_out_network_dir):
            os.makedirs(param_out_network_dir)
        arcpy.CreateFileGDB_management(param_out_network_dir, param_out_gdb)
        arcpy.CopyFeatures_management(lyr_output_feature_class_select, param_out_network)

        # Dissolve and append non-sloped lines
        arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "SWITCH_SELECTION")
        arcpy.Dissolve_management(lyr_output_feature_class_select, lyr_dissolved_lines, "from_;to", "FT_MIN_2D SUM;TF_MIN_2D SUM;FT_MIN_3D SUM;TF_MIN_3D SUM;Avg_Slope SUM;access MAX;area MAX;bridge MAX;highway MAX;junction MAX;landuse MAX;lanes MAX;maxspeed MAX;oneway MAX;name MAX;ref MAX;service MAX;tunnel MAX;width MAX;Length3D SUM", "SINGLE_PART", "UNSPLIT_LINES")
        arcpy.Append_management(lyr_dissolved_lines, param_out_network, "NO_TEST", "", "")


    def interpolate(self, params, standalone=False):

        try:

            # Begin script
            arcpy.AddMessage("## Interpolation begins: {0}".format(self.get_current_timestamp_str()))
            self.delete_in_memory()
            self.check_out_extension()

            # Set parameters
            self.set_interpolation_params(params, standalone)

            # Process: Interpolate Shape
            arcpy.InterpolateShape_3d(param_in_dtm, param_in_network, lyr_interpolated_lines, "", "1", "BILINEAR", "DENSIFY", "0")

            # Process: Add Fields
            self.add_fields_or_calculate(add_field_Z, lyr_interpolated_lines)

            # See if there are No_Split edges specified
            if param_has_no_split_edges:

                ''' Proceed to edges can be split'''

                # Process: Select edges that can be split
                arcpy.MakeFeatureLayer_management(lyr_interpolated_lines, lyr_lines_interpolate_select)
                arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "NEW_SELECTION", query_no_slope, "INVERT")

                # Process: Calculate value of Z for the lines that can be split
                self.add_fields_or_calculate(calculate_field_z, lyr_lines_interpolate_select)

                # Copy features from lines that can be split to a new feature class
                arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_split)

                ''' Proceed to edges cannot be split'''

                # Process: Select Layer By Attribute (edges cannot be split)
                arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "SWITCH_SELECTION")
                arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_nosplit)

                # Process: Calculate 3D attributes for the lines that cannot be split
                arcpy.FeatureTo3DByAttribute_3d(lyr_lines_nosplit, lyr_lines_nosplit_3d, "Start_Z", "End_Z")

                # Process Calculate value of Z for the lines that cannot be split
                self.add_fields_or_calculate(calculate_field_z, lyr_lines_nosplit_3d)

                ''' Combine both split and not split edges'''

                # Append lines that cannot be split to lines that can be split
                arcpy.Append_management(lyr_lines_nosplit_3d, lyr_lines_split, "NO_TEST", "", "")

                # Process: Calculate 3D attributes for the lines that can be split
                self.calculate_3d_attributes(lyr_lines_split)

            # Alternate workflow if no No_Split parameter is set
            else:
                # Process: Calc all 3D attributes
                self.calculate_3d_attributes(lyr_interpolated_lines)

            # Prepare output
            self.simplify_and_generate_output()

            # End process
            self.delete_in_memory()
            self.check_in_extension()
            arcpy.AddMessage("## Interpolation ended: {0}".format(self.get_current_timestamp_str()))

        except Exception as e:
            arcpy.AddMessage("*****" + str(e) + "*****")
            arcpy.AddMessage(traceback.print_tb(e.__traceback__))


class DtmRename(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Rename Dtm Files"
        self.description = "Rename all files in given workspace"
        self.canRunInBackground = True
        self.category = "3D Network"

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            displayName="Input Dtm Directory to Rename",
            name="Input_Workspace",
            datatype=["DEWorkspace"],
            parameterType="Required",
            direction="Input")

        params = [param0]
        return params

    def isLicensed(self):
        return True  # tool can be executed

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return



    def execute(self, parameters, message):
        dir_path = parameters[0].valueAsText
        arcpy.AddMessage("Path: {0}".format(dir_path))
        if os.path.isdir(dir_path):
            arcpy.AddMessage("Directory '{0}' exists, renaming now.".format(dir_path))
            os.chdir(dir_path)
            for src in os.listdir():
                # if path is not a directory or folder
                if not os.path.isdir(src):
                    arr_filename = src.split(".")
                    new_filename = "{0}.{1}".format(replace_vowel(arr_filename[0]), arr_filename[1])
                    os.rename(src, new_filename)
                    arcpy.AddMessage("Renamed '{0}' to '{1}'".format(src, new_filename))
                else:
                    arcpy.AddMessage("'{0}' is a folder, cannot be renamed".format(src))
        else:
            arcpy.AddMessage("Directory '{0}' does not exist, ending script.".format(dir_path))


def replace_vowel(original_word):
    vowels = "aeiou "
    new_word = ""
    for letter in original_word:
        if letter not in vowels:
            new_word += (letter.lower())
    return new_word


def read_cities_list(cities_json_path):
    # Read JSON data
    if cities_json_path:
        with open(cities_json_path, 'r') as f:
            return json.load(f)


def collect_data(cities_list_json, param_folder_path):

    # Loop through json file
    cities_list = cities_list_json["cities"]
    for city in cities_list.keys():
        city_save_name = replace_vowel(city)
        city_places = cities_list[city]
        collect_data_per_city(city, city_save_name, city_places, param_folder_path)


def collect_data_per_city(city_name, city_save_name, city_places, param_folder_path):
    # Set print osm default logs
    ox.config(log_file=False, log_console=True, use_cache=True)
    ox.log("===== Download network from OSM {0} begins =====".format(city_name))

    city_network_name = "osm_{0}".format(city_save_name)
    city_bound_name = "osm_{0}".format(city_save_name)

    # Collect boundaries using city name (or place name)
    # Save city boundaries as shapefile
    city_gdf = ox.gdf_from_place(city_name)
    ox.save_gdf_shapefile(city_gdf, filename=city_bound_name, folder=param_folder_path)

    # Collect network using place names
    # Using retain_all to keep disconnected networks, ie HK Island and Kowloon and Lantau
    # Save network as shapefile
    arcpy.AddMessage(city_places)
    G = ox.graph_from_place(city_places, network_type='walk', retain_all=True)
    ox.save_graph_shapefile(G, filename=city_network_name, folder=param_folder_path)

    ox.log("===== Download end for network from OSM {0} =====".format(city_name))
