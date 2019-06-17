
# --------------------------------
# Name:        Network3DScript.py
# Purpose:
# Author: Christopher D. Higgins, Jimmy Chan
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Created     xx/xx/2019
# ArcGIS Version:   ArcGIS Pro 2.3.3
# Python Version:   3.6
# License:
# --------------------------------

import arcpy
import sys
import json
import CollectDSMFromUsgs, CollectDataFromOsm, Network2DTo3D

__version__ = "0.1"


def collect_data(cities_list_json, param_folder_path):

    # Loop through json file
    cities_list = cities_list_json["cities"]
    for city in cities_list.keys():
        city_name = city.replace(" ", "_")
        city_places = cities_list[city]
        CollectDataFromOsm.collect_data_per_city(city_name, city_places, param_folder_path)

        # Pass parameters to interpolate, add parameter of location name
        params_to_interpolate = sys.argv[3:10]
        params_to_interpolate.append(city_name)
        Network2DTo3D.interpolate(params_to_interpolate, False)


def read_cities_list(cities_json_path):

    global param_cities_json, param_folder_path
    param_cities_json = sys.argv[1]
    param_folder_path = sys.argv[2]

    # Read JSON data
    if cities_json_path:
        with open(cities_json_path, 'r') as f:
            return json.load(f)


def run_main_workflow(*argv):

    if check_input():
    #try:
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
    run_main_workflow(sys.argv)

