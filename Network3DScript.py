
# --------------------------------
# Name: Network3DScript.py
# Purpose: Main file to execute OSM data extraction and 3D interpolation
# Author: Christopher D. Higgins, Ronnie Ma
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Edited:     19/06/2019
# ArcGIS Version:   ArcGIS Pro 2.3.3
# Python Version:   3.6
#
# Using this:
#
# Parameters to input:
# 1 - param_cities_json (String) - Path of json containing cities information
# 2 - param_folder_path (String) - Path to raster output folder
# 3 - param_in_network (String) - Path to OSM road network data folder
# 4 - param_in_raster (String) - Path to raster folder
# 5 - param_sample_distance (Numeric) - Sampling radius for roads to split
# 6 - param_has_no_split_edges (Boolean) - There are edges that cannot be split, such as bridges
# 7 - param_has_no_slope_edges (Boolean) - There are edges that has edges that are not slopes
# 8 - param_out_network (String) - Path to output network folder
# 9 - param_location_save_name (String) - Name of location to save as  (provided from Network3DScript)
#
#  1) Call this as a script
#     python <...Network3DScript.py> <cities_json_path> <folder_path> <param_in_network> <param_in_raster> <param_sample_distance> <param_has_no_split_edges> <param_has_no_slope_edges> <param_out_network>
#     Example:
#     python Network3DScript.py cities.json '\\data' "OSMnx_Walk" "HK_DTM_2m_Clip" 10 True True "Output_Network"
#
# --------------------------------

import arcpy
import sys
import json
import CollectDataFromOsm, Network2DTo3D

__version__ = "0.1"


def replace_vowel(original_word):
    vowels = "aeiou "
    new_word = ""
    for letter in original_word:
        if letter not in vowels:
            new_word += (letter.lower())
    return new_word


def collect_data(cities_list_json, param_folder_path):

    # Loop through json file
    cities_list = cities_list_json["cities"]
    for city_name in cities_list.keys():
        city_save_name = replace_vowel(city_name)
        city_places = cities_list[city_name]
        CollectDataFromOsm.collect_data_per_city(city_name, city_save_name, city_places, param_folder_path)

        # Pass parameters to interpolate, add parameter of location name
        params_to_interpolate = sys.argv[3:9]
        params_to_interpolate.append(city_save_name)
        Network2DTo3D.interpolate(params_to_interpolate, False)


def read_cities_list(cities_json_path):
    # Read JSON data
    if cities_json_path:
        with open(cities_json_path, 'r') as f:
            return json.load(f)


def run_main_workflow(*argv):

    if check_input():
        arcpy.AddMessage("run main workflow")

        param_cities_json = sys.argv[1]
        param_folder_path = sys.argv[2]

        cities_list_json = read_cities_list(param_cities_json)
        collect_data(cities_list_json, param_folder_path)

        arcpy.AddMessage("done")


def check_input():
    # TODO: create function to check input
    return True


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

    print("==================== Script Start ==================")
    run_main_workflow(sys.argv)
    print("==================== Script End ==================")

