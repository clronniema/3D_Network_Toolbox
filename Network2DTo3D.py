
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
#     Network2DTo3D.interpolate(sys.argv[n:n])
#
# --------------------------------

# imports
import arcpy, sys
from datetime import datetime

# parameters hardcoded
query_no_slope = "TUNNEL = 'yes' Or BRIDGE = 'yes'"
search_radius = 0.001
extension_list = ["3D", "Spatial"]
dateTimeObj = datetime.now()
timestamp = dateTimeObj.strftime("%H%M%S")

# parameters provided by user
param_in_raster = None
param_in_network = None
param_sample_distance = None
param_has_no_split = None
param_has_no_slope = None
param_out_network = None
param_out_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Test.gdb/testoutput_{0}".format(timestamp)

# temporary file names
lyr_lines_split = "in_memory\\lyr_lines_split".format(timestamp)
lyr_points_split = "in_memory\\lyr_points_split".format(timestamp)
lyr_interpolated_lines = "in_memory\\lyr_interpolated_lines".format(timestamp)
lyr_lines_nosplit = "in_memory\\lyr_lines_nosplit".format(timestamp)
lyr_lines_nosplit_3d = "in_memory\\lyr_lines_nosplit_3d".format(timestamp)
lyr_lines_interpolate_select = "in_memory\\lyr_lines_interpolate_select".format(timestamp)
lyr_output_feature_class_select = "in_memory\\lyr_output_feature_class_select".format(timestamp)
lyr_output_feature_class = "in_memory\\lyr_output_feature_class".format(timestamp)
lyr_dissolved_lines = "in_memory\\lyr_dissolved_lines".format(timestamp)

# operation names of 3d/4d fields
add_field_Z = "ADD_FIELD_Z"
calculate_field_z = "CALCULATE_FIELD_Z"
add_walktime_field = "ADD_WALKTIME_FIELD"
calculate_walktime_field = "CALCULATE_WALKTMIE_FIELD"
add_circle_segment = "ADD_CIRCLE_SEGMENT"
calculate_circle_segment = "CALCULATE_CIRCLE_SEGMENT"


def set_interpolation_params(params=None):
    # Retrieve user entered parameters
    global param_in_raster, param_in_network, param_sample_distance, param_has_no_split, param_has_no_slope, param_out_network
    if params is None:
        params = sys.argv

    # global param_in_raster = params[1]
    # global param_in_network = params[2]
    # global param_sample_distance = params[3]
    # global param_has_no_split = params[4]
    # global param_has_no_slope = params[5]
    # global param_out_network = params[6] + "_" + timestamp

    # param_in_raster = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "HK_DTM_2m"
    param_in_raster = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "HK_DTM_2m_Clip"
    param_in_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Project.gdb/" + "OSMnx_Walk"
    param_sample_distance = float('10')
    param_has_no_split = True
    param_has_no_slope = True
    param_out_network = "D:/workspace/network_toolbox/3D_Networks_Project/3D_Networks_Test.gdb/testoutput_{0}".format(timestamp)


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
    if param_sample_distance is None:
        arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE", 10, "", "")
    else:
        arcpy.GeneratePointsAlongLines_management(lines_layer, lyr_points_split, "DISTANCE",
                                                  float(param_sample_distance), "", "")


def add_fields_or_calculate(case, param=None):
    if case == add_field_Z:
        arcpy.management.AddFields(param,
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
        arcpy.management.CalculateGeometryAttributes(param, "Start_X LINE_START_X;Start_Y LINE_START_Y;End_X LINE_END_X;End_Y LINE_END_Y;Start_Z LINE_START_Z;End_Z LINE_END_Z", None, None, None)
        arcpy.management.CalculateFields(param,
                                         "PYTHON3",
                                         "Max_Z 'max(!Start_Z!, !End_Z!)';",
                                         None)
        return
    elif case == add_walktime_field:
        arcpy.management.AddFields(param,
                                   "FT_MIN_2D DOUBLE # # # #;"
                                   "TF_MIN_2D DOUBLE # # # #;"
                                   "FT_MIN_3D DOUBLE # # # #;"
                                   "TF_MIN_3D DOUBLE # # # #;"
                                   )
        return
    elif case == calculate_walktime_field:
        arcpy.management.CalculateFields(param,
                                         "PYTHON3",
                                         "FT_MIN_2D (!shape.length!/(5036.742125))*60;"
                                         "TF_MIN_2D (!shape.length!/(5036.742125))*60;"
                                         "FT_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!End_Z!-!Start_Z!)/(!shape.length!)+0.05)))))*1000))*60;"
                                         "TF_MIN_3D (!Length3D!/((6*(math.exp((-3.5)*(math.fabs((!Start_Z!-!End_Z!)/(!shape.length!)+0.05)))))*1000))*60;",
                                         None)
        return
    elif case == add_circle_segment:
        arcpy.management.AddFields(param,
                                   "SEGMENT_ID LONG # # # #;"
                                   )

        return
    elif case == calculate_circle_segment:
        arcpy.management.CalculateField(param, "SEGMENT_ID", "!OBJECTID!", "PYTHON3", None)
    return


def replace_no_slope_lines():
    if param_has_no_slope:
        arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "NEW_SELECTION", query_no_slope)
        arcpy.management.CalculateFields(lyr_output_feature_class_select, "PYTHON3", "FT_MIN_3D !FT_MIN_2D!;TF_MIN_3D !TF_MIN_2D!", None)


def calculate_3d_attributes(lines_layer):
    # Generate Points Along Lines
    generate_points_along_lines(lines_layer)

    # Split Lines at Points
    arcpy.SplitLineAtPoint_management(lines_layer, lyr_points_split, lyr_output_feature_class, search_radius)
    add_fields_or_calculate(calculate_field_z, lyr_output_feature_class)

    # Add SEGMENT_ID to circular lines
    add_fields_or_calculate(add_circle_segment, lyr_output_feature_class)
    add_fields_or_calculate(calculate_circle_segment, lyr_output_feature_class)

    # Add Z Information
    arcpy.AddZInformation_3d(lyr_output_feature_class, "LENGTH_3D;AVG_SLOPE", "NO_FILTER")

    # Add walk time fields
    add_fields_or_calculate(add_walktime_field, lyr_output_feature_class)

    # Calculate walk time fields
    add_fields_or_calculate(calculate_walktime_field, lyr_output_feature_class)

    # MakeFeatureLayer - temp output_feature_class_lyr
    arcpy.MakeFeatureLayer_management(lyr_output_feature_class, lyr_output_feature_class_select)

    # Replace 3D walk time with 2D walk time for any No_Slope lines
    replace_no_slope_lines()
    return


def split_circles_2(in_layer):
    lyr_simplify = "in_memory\\lyr_simplify"
    lyr_simplify_select = "in_memory\\lyr_simplify_select"
    lyr_simplify_pts = "in_memory\\lyr_simplify_pts"
    lyr_simplify_circles = "in_memory\\lyr_simplify_circles"
    lyr_simplify_circles_pts = "in_memory\\lyr_simplify_circles_pts"
    lyr_simplpify_circles_split = "in_memory\\lyr_simplpify_circles_split"
    lyr_interpolted_shape = "in_memory\\lyr_interpolted_shape"

    # Create midpoints for circular lines
    arcpy.MakeFeatureLayer_management(in_layer, lyr_simplify_select)
    arcpy.management.SelectLayerByAttribute(lyr_simplify_select, "NEW_SELECTION", "Start_X = End_X And Start_Y = End_Y", None)
    arcpy.management.GeneratePointsAlongLines(lyr_simplify_select, lyr_simplify_pts, "PERCENTAGE", None, 50, None)
    arcpy.management.SplitLineAtPoint(lyr_simplify_select, lyr_simplify_pts, lyr_simplify_circles, "0.001 Meters")
    arcpy.management.AddField(lyr_simplify_circles, "SegmentID", "LONG", None, None, None, None, "NULLABLE", "NON_REQUIRED", None)
    arcpy.management.CalculateField(lyr_simplify_circles, "SegmentID", "!OBJECTID!", "PYTHON3", None)
    arcpy.management.GeneratePointsAlongLines(lyr_simplify_circles, lyr_simplify_circles_pts, "DISTANCE", "10 Meters", None, None)
    arcpy.management.SplitLineAtPoint(lyr_simplify_circles, lyr_simplify_circles_pts, lyr_simplpify_circles_split, "0.001 Meters")
    arcpy.ddd.InterpolateShape(param_in_raster, lyr_simplpify_circles_split, lyr_interpolted_shape, None, 1, "BILINEAR", "DENSIFY", 0, "EXCLUDE")
    arcpy.management.CalculateField(lyr_interpolted_shape, "Avg_Slope", "(!shape.lastpoint.Z! - !shape.firstpoint.Z!)/!shape.length!", "PYTHON3", None)


def split_circles():
    lyr_simplify = "in_memory\\lyr_simplify"
    lyr_simplify_select = "in_memory\\lyr_simplify_select"
    lyr_simplify_pts = "in_memory\\lyr_simplify_pts"
    lyr_simplify_circles = "in_memory\\lyr_simplify_circles"
    lyr_simplify_circles_pts = "in_memory\\lyr_simplify_circles_pts"
    lyr_simplpify_circles_split = "in_memory\\lyr_simplpify_circles_split"
    lyr_interpolted_shape = "in_memory\\lyr_interpolted_shape"

    # Create midpoints for circular lines
    arcpy.MakeFeatureLayer_management(lyr_simplify, lyr_simplify_select)
    arcpy.management.SelectLayerByAttribute(lyr_simplify_select, "NEW_SELECTION", "Start_X = End_X And Start_Y = End_Y", None)
    arcpy.management.GeneratePointsAlongLines(lyr_simplify_select, lyr_simplify_pts, "PERCENTAGE", None, 50, None)
    arcpy.management.SplitLineAtPoint(lyr_simplify_select, lyr_simplify_pts, lyr_simplify_circles, "0.001 Meters")
    arcpy.management.AddField(lyr_simplify_circles, "SegmentID", "LONG", None, None, None, None, "NULLABLE", "NON_REQUIRED", None)
    arcpy.management.CalculateField(lyr_simplify_circles, "SegmentID", "!OBJECTID!", "PYTHON3", None)
    arcpy.management.GeneratePointsAlongLines(lyr_simplify_circles, lyr_simplify_circles_pts, "DISTANCE", "10 Meters", None, None)
    arcpy.management.SplitLineAtPoint(lyr_simplify_circles, lyr_simplify_circles_pts, lyr_simplpify_circles_split, "0.001 Meters")
    arcpy.ddd.InterpolateShape(param_in_raster, lyr_simplpify_circles_split, lyr_interpolted_shape, None, 1, "BILINEAR", "DENSIFY", 0, "EXCLUDE")
    arcpy.management.CalculateField(lyr_interpolted_shape, "Avg_Slope", "(!shape.lastpoint.Z! - !shape.firstpoint.Z!)/!shape.length!", "PYTHON3", None)



def simplify_and_generate_output():

    # Copy lines with slope to output layer -- avoid circular segments (those with SEGMENT_ID)
    arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "NEW_SELECTION", "AVG_SLOPE <> 0 and SEGMENT_ID is not null")
    arcpy.CopyFeatures_management(lyr_output_feature_class_select, param_out_network)

    # Dissolve and append non-sloped lines
    arcpy.SelectLayerByAttribute_management(lyr_output_feature_class_select, "SWITCH_SELECTION")
    arcpy.Dissolve_management(lyr_output_feature_class_select, lyr_dissolved_lines, "from_;to", "FT_MIN_2D SUM;TF_MIN_2D SUM;FT_MIN_3D SUM;TF_MIN_3D SUM;Avg_Slope SUM;access MAX;area MAX;bridge MAX;highway MAX;junction MAX;landuse MAX;lanes MAX;maxspeed MAX;oneway MAX;name MAX;ref MAX;service MAX;tunnel MAX;width MAX;Length3D SUM", "SINGLE_PART", "UNSPLIT_LINES")
    arcpy.Append_management(lyr_dissolved_lines, param_out_network, "NO_TEST", "", "")


def interpolate(params):

    # Begin script
    arcpy.AddMessage("Interpolation begins")
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

        # Process: Select edges that can be split
        arcpy.MakeFeatureLayer_management(lyr_interpolated_lines, lyr_lines_interpolate_select)
        arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "NEW_SELECTION", query_no_slope, "INVERT")
        arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_split)

        # Process: Calc all 3D attributes
        calculate_3d_attributes(lyr_lines_split)

        # Process: Select Layer By Attribute (edges cannot be split)
        arcpy.SelectLayerByAttribute_management(lyr_lines_interpolate_select, "SWITCH_SELECTION")
        arcpy.CopyFeatures_management(lyr_lines_interpolate_select, lyr_lines_nosplit)

        # Process No_Split edges / Calculate value of Z
        add_fields_or_calculate(calculate_field_z, lyr_lines_nosplit)

        # Feature To 3D By Attribute for No_Split edges
        arcpy.FeatureTo3DByAttribute_3d(lyr_lines_nosplit, lyr_lines_nosplit_3d, "Start_Z", "End_Z")

        # Append split and no_split lines
        arcpy.Append_management(lyr_lines_nosplit_3d, lyr_output_feature_class, "NO_TEST", "", "")
        arcpy.AddMessage("Finished processing data with 'No Split' flag")


    # Alternate workflow if no No_Split parameter is set
    else:
        # Process: Calc all 3D attributes
        calculate_3d_attributes(lyr_interpolated_lines)
        arcpy.AddMessage("Finished processing data without 'No Split' flag")

    # Prepare output
    simplify_and_generate_output()

    delete_in_memory()
    check_in_extension()
    arcpy.AddMessage("Interpolation ended")

if __name__ == "__main__":
    # execute only if run as a script
    interpolate(sys.argv)

