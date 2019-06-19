# --------------------------------
# Name: CollectDataFromOsm.py
# Purpose: Extraction of OSM data based on location names
# Author: Christopher D. Higgins, Ronnie Ma
# Institution: The Hong Kong Polytechnic University
# Department: Department of Land Surveying and Geo-Informatics
# Edited:     14/06/2019
# ArcGIS Version:   ArcGIS Pro 2.3.3
# Python Version:   3.6
#
# Using this:
#
# Parameters to input:
# 1 - param_cities_json (String) - Path of json containing cities information
# 2 - param_folder_path (String) - Path to raster output folder
#
#  1) Call this as a script
#     python <...CollectDataFromOsm.py> <param_cities_json> <param_folder_path>
#     Example:
#     python CollectDataFromOsm.py cities.json '\\data'
#
#  2) Import script and pass parameters
#     import Network2DTo3D
#     Network2DTo3D.download(cities_json_path)
#

# --------------------------------

import osmnx as ox
import json
import sys

param_cities_json = None
param_folder_path = None


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
        city_name = replace_vowel(city)
        city_places = cities_list[city]
        collect_data_per_city(city_name, city_places, param_folder_path)


def collect_data_per_city(city_name, city_save_name, city_places, param_folder_path):
    # Set print osm default logs
    ox.config(log_file=True, log_console=True, use_cache=True)
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
    G = ox.graph_from_place(city_places, network_type='walk', retain_all=True)
    ox.save_graph_shapefile(G, filename=city_network_name, folder=param_folder_path)

    ox.log("===== Download end for network from OSM {0} =====".format(city_name))


def download_data(params):

    # Could be called from outside
    # Main workflow for downloading data
    global param_cities_json, param_folder_path
    param_cities_json = params[0]
    param_folder_path = params[1]

    cities_list_json = read_cities_list(param_cities_json)
    collect_data(cities_list_json, param_folder_path)


if __name__ == "__main__":
    # Execute through this only if run as standalone script
    download_data(sys.argv[1:3])

