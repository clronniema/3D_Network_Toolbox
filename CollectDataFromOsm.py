
import osmnx as ox
import geopandas as gpd
import networkx as nx
import matplotlib.cm as cm
import matplotlib.colors as colors
import pandas as pd
import numpy as np
import requests
import CitiesList

def printMsg(msg):
    print("CollectDataFromOsm msg: {0}".format(msg))


def collect_data(cities_list):
    ox.config(log_file=True, log_console=True, use_cache=True)

    for city_array in cities_list:
        city_osm_name = city_array[0]
        city_raster_name = city_array[1] + ""
        city_network_name = "network_{0}.shp".format(city_array[1])
        city_bound_name = "boundary_{0}.shp".format(city_array[1])

        # gdf is a geopandas GeoDataFrame
        city = ox.gdf_from_place('Hong Kong, Hong Kong')
        #fig, ax = ox.plot_shape(city, figsize=(3, 3))

        # now use the city polygon to extract streets from OSM
        # the projection will take some time - can leave it running and do something else
        city_polygon = city['geometry'].iloc[0]
        G4 = ox.graph_from_polygon(city_polygon, network_type='walk')
        #G4_projected = ox.project_graph(G4)

        #fig, ax = ox.plot_graph(G4_projected)

        # save the Hong Kong boundary polygon as a shapefile
        ox.save_gdf_shapefile(city_polygon, folder='D:\\workspace\\network_toolbox\\3D_Networks_Project\\3D_Network_TestFolder\\data', filename=city_bound_name)
        # Save the Hong Kong street network as ESRI shapefile to work with in GIS
        ox.save_graph_shapefile(G4, folder='D:\\workspace\\network_toolbox\\3D_Networks_Project\\3D_Network_TestFolder\\data', filename=city_network_name)


def read_cities_list():
    return CitiesList.cities


if __name__ == "__main__":
    # Execute only if run as standalone script
    cities_list = read_cities_list()
    collect_data(cities_list)
