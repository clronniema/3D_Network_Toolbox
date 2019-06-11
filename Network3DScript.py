
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

import arcpy, sys
import CollectDSMFromUsgs, CollectDataFromOsm, Network2DTo3D

__version__ = "0.1"

def run_main_workflow(*argv):

    if check_input():
    #try:
        arcpy.AddMessage("run main workflow")
        CollectDSMFromUsgs.printMsg("CollectDSMFromUsgs")
        CollectDataFromOsm.printMsg("CollectDataFromOsm")
        Network2DTo3D.interpolate(sys.argv[1:7])
        arcpy.AddMessage("done")
    #pass
    # except arcpy.ExecuteError:
    #     arcpy.AddError(arcpy.GetMessages(2))
    #     print(arcpy.GetMessages(2))
    # except Exception as e:
    #     arcpy.AddError(e.args[0])
    #     print(e.args[0])


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

