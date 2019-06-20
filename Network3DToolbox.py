
# --------------------------------
# Name: Network3DToolbox.py
# Purpose: Main file to execute OSM data extraction and 3D interpolation
# Author: Christopher D. Higgins, Ronnie Ma
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Edited:     19/06/2019
#
# Using this:
#
# Parameters to input:
# 1 - param_cities_json (String) - Path of json containing cities information
# 2 - param_osm_shp_folder (String) - Path to city boundaries and network output folder, a folder named "data" will be created
# 3 - param_in_dtm (String) - Path to DTM folder
# 4 - param_sample_distance (Numeric) - Sampling radius for roads to split
# 5 - param_has_no_split_edges (Boolean) - There are edges that cannot be split, such as bridges
# 6 - param_has_no_slope_edges (Boolean) - There are edges that has edges that are not slopes
# 7 - param_out_network (String) - Path to output network folder
#
#  1) Call this as a script
# Order of parameters input
# python <...Network3DToolbox.py> <Input Cities JSON File> <OSM City Shapefile Output Folder> <Input Surface Folder> <Sample Distance> <Network has No Split edges> <Network has No Slope edges> <Output 3D Network Folder>
# Example:
# cd D:\network_workspace
# python D:\3D_Networks_Project\Network3DToolbox.py cities.json osm_extract dtm_folder 10 True True 3d_out_networks
#
# --------------------------------

import arcpy
import sys
import json
import CollectDataFromOsm, NetworkInterpolation

__version__ = "0.1"


def replace_vowel(original_word):
    vowels = "aeiou "
    new_word = ""
    for letter in original_word:
        if letter not in vowels:
            new_word += (letter.lower())
    return new_word


def collect_data(cities_list_json, param_osm_shp_folder):

    # Loop through json file
    cities_list = cities_list_json["cities"]
    for city_name in cities_list.keys():
        city_save_name = replace_vowel(city_name)
        city_places = cities_list[city_name]
        CollectDataFromOsm.collect_data_per_city(city_name, city_save_name, city_places, param_osm_shp_folder)

        # Pass parameters to interpolate, add parameter of location name
        params_to_interpolate = sys.argv[2:8]
        params_to_interpolate.append(city_save_name)
        NetworkInterpolation.interpolate(params_to_interpolate, False)


def read_cities_list(cities_json_path):
    # Read JSON data
    if cities_json_path:
        with open(cities_json_path, 'r') as f:
            return json.load(f)


def run_main_workflow(params):

    arcpy.AddMessage("== Run tool ==")
    param_cities_json = params[1]
    param_osm_shp_folder = params[2] + "/data"

    cities_list_json = read_cities_list(param_cities_json)
    collect_data(cities_list_json, param_osm_shp_folder)

    arcpy.AddMessage("== Tool Run Complete ==")


# This test allows the script to be used from the operating
# system command prompt (stand-alone), in a Python IDE,
# as a geoprocessing script tool, or as a module imported in
# another script

if __name__ == '__main__':

    # Main Workflow
    # 0.1. Get city list
    # 1. Collect network data from OSM
    # 2. Collect DSM from USGS
    # 3. Interpolate!
    params = [
        "",
        arcpy.GetParameterAsText(0),
        arcpy.GetParameterAsText(1),
        arcpy.GetParameterAsText(2),
        arcpy.GetParameterAsText(3),
        arcpy.GetParameter(4),
        arcpy.GetParameter(5),
        arcpy.GetParameterAsText(6)
    ]

    print("==================== Script Start ==================")
    run_main_workflow(params)
    print("==================== Script End ====================")
