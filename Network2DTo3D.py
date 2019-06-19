
# --------------------------------
# Name: Network2DTo3D.py
# Purpose: Script to do 3D interpolation of road network based on DEM
# Author: Christopher D. Higgins, Jimmy Chan, Ronnie Ma
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Edited: 19/06/2019
# ArcGIS Version:   ArcGIS Pro 2.3.3
# Python Version:   3.6
#
# Using this:
#
# [Standalone] Parameters to input:
# 1 - param_in_network (String) - Path to OSM road network
# 2 - param_in_raster (String) - Path to raster file
# 3 - param_sample_distance (Numeric) - Sampling radius for roads to split
# 4 - param_has_no_split_edges (Boolean) - There are edges that cannot be split, such as bridges
# 5 - param_has_no_slope_edges (Boolean) - There are edges that has edges that are not slopes
# 6 - param_out_network (String) - Path to output network file
#
# [With Network3DScript] Parameters to input:
# 1 - param_in_network (String) - Path to OSM road network data folder
# 2 - param_in_raster (String) - Path to raster folder
# 3 - param_sample_distance (Numeric) - Sampling radius for roads to split
# 4 - param_has_no_split_edges (Boolean) - There are edges that cannot be split, such as bridges
# 5 - param_has_no_slope_edges (Boolean) - There are edges that has edges that are not slopes
# 6 - param_out_network (String) - Path to output network folder
# 7 - param_location_save_name (String) - Name of location to save as  (provided from Network3DScript)
#
#  1) Call this as a script
#     python <...Network2DTo3D.py> <param_in_network> <param_in_raster> <param_sample_distance> <param_has_no_split_edges> <param_has_no_slope_edges> <param_out_network>
#     Example:
#     python Network2DTo3D.py "OSMnx_Walk" "HK_DTM_2m_Clip" 10 True True "Output_Network"
#
#  2) Import script and pass parameters
#     import Network2DTo3D
#     Network2DTo3D.interpolate(sys.argv[n:m])
#

# --------------------------------


# imports
import arcpy
import sys
from datetime import datetime
import os

# parameters hardcoded
query_no_slope = "TUNNEL = 'yes' Or BRIDGE = 'yes'"
search_radius = 0.001
extension_list = ["3D", "Spatial"]
date_time_obj = datetime.now()
timestamp = date_time_obj.strftime("%H%M%S")

# parameters provided by user
param_in_raster = None
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


def get_current_timestamp_str():
    date_time = datetime.now()
    return date_time.strftime("%m/%d/%Y %H:%M:%S")


def set_interpolation_params(params, standalone=False):
    # Retrieve user entered parameters
    global param_in_raster, param_in_network, param_sample_distance, param_has_no_split_edges, param_has_no_slope_edges, param_out_network_dir, param_location_save_name, param_out_gdb, param_out_network
    if params is None:
        params = sys.argv

    if standalone:
        param_in_network = params[0]
        param_in_raster = params[1]
        param_sample_distance = params[2]
        param_has_no_split_edges = params[3]
        param_has_no_slope_edges = params[4]
        #param_out_network_dir = params[5] + "_" + timestamp
        param_out_network_dir = "{0}/output/network".format(params[5])
        param_out_gdb = "{0}_{1}.gdb".format(param_location_save_name, timestamp)
        param_out_network = param_out_network_dir + "/" + param_out_gdb + "/network"
    else:
        param_location_save_name = params[6]
        param_in_network = "{0}/data/osm_{1}/edges/edges.shp".format(params[0], param_location_save_name)
        param_in_raster = "{0}/data/raster/{1}".format(params[1], param_location_save_name)
        param_sample_distance = params[2]
        param_has_no_split_edges = params[3]
        param_has_no_slope_edges = params[4]
        param_out_network_dir = "{0}/output/network".format(params[5])
        param_out_gdb = "{0}.gdb".format(param_location_save_name)
        param_out_network = param_out_network_dir + "/" + param_out_gdb + "/network"

    #Parameters for testing only

    '''
    param_in_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "OSMnx_Walk"
    param_in_raster = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "HK_DTM_2m_Clip"
    param_sample_distance = float('10')
    param_has_no_split = True
    param_has_no_slope = True
    param_out_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Test.gdb/testoutput_{0}".format(timestamp)
    '''


def check_out_extension():
    for extension in extension_list:
        arcpy.CheckOutExtension(extension)
    return


def check_in_extension():
    for extension in extension_list:
        arcpy.CheckInExtension(extension)
    return


def delete_in_memory():
    # Delete in-memory table
    arcpy.Delete_management("in_memory\\{0}".format(timestamp))
    return


def generate_points_along_lines(lines_layer):
    try:
        arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE",
                                                  float(param_sample_distance), "", "")
    except ValueError:
        arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE", 10, "", "")


def add_fields_or_calculate(case, param_lyr=None):
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


def replace_no_slope_edges():
    if param_has_no_slope_edges:
        arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "NEW_SELECTION", query_no_slope)
        arcpy.CalculateFields_management(lyr_output_feature_class_select, "PYTHON3", "FT_MIN_3D !FT_MIN_2D!;TF_MIN_3D !TF_MIN_2D!", None)


def calculate_3d_attributes(lines_layer):

    # Add SEGMENT_ID to circular lines
    arcpy.MakeFeatureLayer_management(lines_layer, lyr_lines_select)
    add_fields_or_calculate(add_circle_segment, lyr_lines_select)
    add_fields_or_calculate(calculate_circle_segment, lyr_lines_select)

    # Generate Points Along Lines
    generate_points_along_lines(lyr_lines_select)

    # Split Lines at Points
    arcpy.SplitLineAtPoint_management(lyr_lines_select, lyr_points_split, lyr_output_feature_class, search_radius)
    add_fields_or_calculate(calculate_field_z, lyr_output_feature_class)

    # Add Z Information
    arcpy.AddZInformation_3d(lyr_output_feature_class, "LENGTH_3D;AVG_SLOPE", "NO_FILTER")

    # Add walk time fields
    add_fields_or_calculate(add_walktime_field, lyr_output_feature_class)

    # Calculate walk time fields
    add_fields_or_calculate(calculate_walktime_field, lyr_output_feature_class)

    # MakeFeatureLayer - temp output_feature_class_lyr
    arcpy.MakeFeatureLayer_management(lyr_output_feature_class, lyr_output_feature_class_select)

    # Replace 3D walk time with 2D walk time for any No_Slope lines
    replace_no_slope_edges()
    return


def simplify_and_generate_output():

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


def interpolate(params, standalone=False):

    try:

        # Begin script
        arcpy.AddMessage("Interpolation begins: {0}".format(get_current_timestamp_str()))
        delete_in_memory()
        check_out_extension()

        # Set parameters
        set_interpolation_params(params, standalone)

        # Process: Interpolate Shape
        arcpy.InterpolateShape_3d(param_in_raster, param_in_network, lyr_interpolated_lines, "", "1", "BILINEAR", "DENSIFY", "0")

        # Process: Add Fields
        add_fields_or_calculate(add_field_Z, lyr_interpolated_lines)

        # See if there are No_Split edges specified
        if param_has_no_split_edges:

            ''' Proceed to edges can be split'''

            # Process: Select edges that can be split
            arcpy.MakeFeatureLayer_management(lyr_interpolated_lines, lyr_lines_interpolate_select)
            arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "NEW_SELECTION", query_no_slope, "INVERT")

            # Process: Calculate value of Z for the lines that can be split
            add_fields_or_calculate(calculate_field_z, lyr_lines_interpolate_select)

            # Copy features from lines that can be split to a new feature class
            arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_split)

            ''' Proceed to edges cannot be split'''

            # Process: Select Layer By Attribute (edges cannot be split)
            arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "SWITCH_SELECTION")
            arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_nosplit)

            # Process: Calculate 3D attributes for the lines that cannot be split
            arcpy.FeatureTo3DByAttribute_3d(lyr_lines_nosplit, lyr_lines_nosplit_3d, "Start_Z", "End_Z")

            # Process Calculate value of Z for the lines that cannot be split
            add_fields_or_calculate(calculate_field_z, lyr_lines_nosplit_3d)

            ''' Combine both split and not split edges'''

            # Append lines that cannot be split to lines that can be split
            arcpy.Append_management(lyr_lines_nosplit_3d, lyr_lines_split, "NO_TEST", "", "")

            # Process: Calculate 3D attributes for the lines that can be split
            calculate_3d_attributes(lyr_lines_split)

        # Alternate workflow if no No_Split parameter is set
        else:
            # Process: Calc all 3D attributes
            calculate_3d_attributes(lyr_interpolated_lines)

        # Prepare output
        simplify_and_generate_output()

        # End process
        delete_in_memory()
        check_in_extension()
        arcpy.AddMessage("Interpolation ended: {0}".format(get_current_timestamp_str()))

    except Exception as e:
        arcpy.AddMessage("*****" + str(e) + "*****")


if __name__ == "__main__":
    # Execute only if run as standalone script
    interpolate(sys.argv[1:7])
