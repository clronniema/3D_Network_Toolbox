
# --------------------------------
# Name:        Network2DTo3D.py
# Purpose:
# Author: Christopher D. Higgins, Jimmy Chan
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Created     xx/xx/2019
# ArcGIS Version:   ArcGIS Pro 2.3.3
# Python Version:   3.6
# License:
#
#
#  Using this:
#
#  1) Call this as a script
#     i.e. python Network2DTo3D param1 param2...
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
param_has_no_split = None
param_has_no_slope = None
param_out_network = None

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


def set_interpolation_params(params=None):
    # Retrieve user entered parameters
    global param_in_raster, param_in_network, param_sample_distance, param_has_no_split, param_has_no_slope, param_out_network
    if params is None:
        params = sys.argv

    param_in_raster = params[0]
    param_in_network = params[1]
    param_sample_distance = params[2]
    param_has_no_split = params[3]
    param_has_no_slope = params[4]
    param_out_network = params[5] + "_" + timestamp

    #Parameters for testing only

    '''
    param_in_raster = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "HK_DTM_2m_Clip"
    param_in_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "OSMnx_Walk"
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


def add_fields_or_calculate(case, param=None):
    if case == add_field_Z:
        arcpy.AddFields_management(param,
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
        arcpy.CalculateGeometryAttributes_management(param, "Start_X LINE_START_X;Start_Y LINE_START_Y;End_X LINE_END_X;End_Y LINE_END_Y;Start_Z LINE_START_Z;End_Z LINE_END_Z", None, None, None)
        arcpy.CalculateFields_management(param,
                                         "PYTHON3",
                                         "Max_Z 'max(!Start_Z!, !End_Z!)';",
                                         None)
        return
    elif case == add_walktime_field:
        arcpy.AddFields_management(param,
                                   "FT_MIN_2D DOUBLE # # # #;"
                                   "TF_MIN_2D DOUBLE # # # #;"
                                   "FT_MIN_3D DOUBLE # # # #;"
                                   "TF_MIN_3D DOUBLE # # # #;"
                                   )
        return
    elif case == calculate_walktime_field:
        arcpy.CalculateFields_management(param,
                                         "PYTHON3",
                                         "FT_MIN_2D (!shape.length!/(5036.742125))*60;"
                                         "TF_MIN_2D (!shape.length!/(5036.742125))*60;"
                                         "FT_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*1000))*60;"
                                         "TF_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*1000))*60;",
                                         None)
        return
    elif case == add_circle_segment:
        arcpy.AddFields_management(param,
                                   "SEGMENT_ID LONG # # # #;"
                                   )

        return
    elif case == calculate_circle_segment:
        arcpy.SelectLayerByAttribute_management(param, "NEW_SELECTION", "Start_X = End_X And Start_Y = End_Y", None)
        arcpy.CalculateField_management(param, "SEGMENT_ID", "!OBJECTID!", "PYTHON3", None)
        arcpy.SelectLayerByAttribute_management(param, "CLEAR_SELECTION")

    return


def replace_no_slope_edges():
    if param_has_no_slope:
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
    arcpy.CopyFeatures_management(lyr_output_feature_class_select, param_out_network)

    # Dissolve and append non-sloped lines
    arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "SWITCH_SELECTION")
    arcpy.Dissolve_management(lyr_output_feature_class_select, lyr_dissolved_lines, "from_;to", "FT_MIN_2D SUM;TF_MIN_2D SUM;FT_MIN_3D SUM;TF_MIN_3D SUM;Avg_Slope SUM;access MAX;area MAX;bridge MAX;highway MAX;junction MAX;landuse MAX;lanes MAX;maxspeed MAX;oneway MAX;name MAX;ref MAX;service MAX;tunnel MAX;width MAX;Length3D SUM", "SINGLE_PART", "UNSPLIT_LINES")
    arcpy.Append_management(lyr_dissolved_lines, param_out_network, "NO_TEST", "", "")


def interpolate(params):

    try:

        # Begin script
        arcpy.AddMessage("Interpolation begins: {0}".format(get_current_timestamp_str()))
        delete_in_memory()
        check_out_extension()

        # Set parameters
        set_interpolation_params(params)

        # Process: Interpolate Shape
        arcpy.InterpolateShape_3d(param_in_raster, param_in_network, lyr_interpolated_lines, "", "1", "BILINEAR", "DENSIFY", "0")

        # Process: Add Fields
        add_fields_or_calculate(add_field_Z, lyr_interpolated_lines)

        # See if there are No_Split edges specified
        if param_has_no_split:

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
        arcpy.AddMessage(str(e))


if __name__ == "__main__":
    # Execute only if run as standalone script
    interpolate(sys.argv)
