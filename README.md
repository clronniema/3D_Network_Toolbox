# 3D Network Toolbox

Using an input pedestrian network and a Digital Elevation/Terrain Model (DEM/DTM), this Python script for ArcGIS Pro implements Tobler’s Hiking Function to enable the calculation of slope-aware travel times for walking travel on a 3D network.

<img width="500" alt="3d_network" src="/assets/img/3D_NetworkToolbox.jpg">

## Overview

This script performs several processes:
1) Extract pedestrian network of cities from OSM
2) Interpolate the 3D shape of the network given the DTM
3) Split the original network edges into smaller segments
4) Calculate the average slope of these segments
5) Calculate the estimated pedestrian velocity given the slope of the terrain

Options are given to control the granularity of results and specify any edges you do not want to be split or not have slope-aware travel times. See the detailed explanation below. This tool is adapted from [Higgins (2019)](https://doi.org/10.1016/j.landurbplan.2018.12.011).

## About
### Authors
**Christopher D. Higgins**  
Department of Land Surveying and Geo-informatics  
Department of Building and Real Estate  
The Hong Kong Polytechnic University

**Jimmy Chan**  
Department of Land Surveying and Geo-informatics  
The Hong Kong Polytechnic University


If used for research purposes, please cite as:

```
@techreport{higgins2018,
  Title    = {3D Network Toolbox},
  Author   = {Higgins, Christopher D. and Chan, Jimmy},
  Year     = {2018}
}
```

###  Version

Version 1.1
- Extracts pedestrian network through OSMnx
- Special case handling, such as lines with same start and end points

Version 1.0
- Tool requires the 3D Analyst and Spatial Analyst extensions  
- Network analysis requires the Network Analyst extension  
- The tool presently only works with **metric** units and is coded to expect values in **meters**


## Detailed Workflow

The OSMnx tool (Boeing, 2017) makes the collection and preparation of OpenStreetMap networks particularly easy. With a list of cities, this script automates the procedure of downloading 2D road network from OpenStreetMap. Currently, only "walk" networks are extracted.

With the extracted 2D OSM networks and Digital Elevation/Terrain Model (DTM), this toolbox interpolates the 3D shape of the network on the DTM. The tool then splits the network into smaller segments and determines the average slope of these segments based on their start and end point XYZ-coordinates. 3D lengths for each line are also interpolated. Next, the tool estimates the travel time in minutes to traverse the segment given the average slope using Tobler’s (1993) Hiking Function:

>  *v* = 6exp(-3.5|*m* + 0.05|)

where *m* is the gradient of the terrain, defined as either *tan*(*θ*) with *θ* as the slope of the terrain in degrees or *dh*/*dx* with *dh* and *dx* as the change in height and distance respectively. This results in the following travel time function:

<img width="500" alt="toblerfunction" src="/assets/img/ToblerFunction.jpg">

The offset in Tobler’s function specifies a maximum walking velocity of 1.67 meters per second (6kph) when walking on a slight downhill gradient of -5%. On flat ground, pedestrian velocity is 1.4 meters per second, or 5kph. Because of the directionality in Tobler's function, walk times are calculated for the From-To (FT) and To-From (TF) directions for network edges.

## How to use 3D Network Toolbox
### Data Preparation
- Prepare a JSON File: A JSON file containing the list of cities to download. The arrays within each city is to download road networks of separated parts of the city. For example, the Hong Kong Island and Lantau Island are members of the array as they are disconnected parts of Hong Kong. A sample is listed below:
``` json
{
  "cities": {
    "Hong Kong": [
      "Hong Kong, Hong Kong",
      "Lantau Island, Hong Kong",
      "Southern District, Hong Kong"
    ],
    "Winnipeg":[
        "Winnipeg, Canada"
    ]
  }
}
```
- Prepare DTM files as TIFF and name them based on the city, replacing all vowels and space. For example "Hong Kong.tif" should be renamed as "hngkng.tif". You may use the tool "Rename Dtm Files" and provide a directory to rename all files within. 


### Environment Prerequisites
- Python packages
    - osmnx ([Installation Guideline](https://osmnx.readthedocs.io/en/stable/#installation))
    - arcpy (Shipped with ArcGIS Pro)

### Script Inputs

- **Input Cities JSON File**: A JSON file containing the list of cities to download, as specified in prerequisites
- **New OSM Cities Output Folder**: Folder to export and store city boundaries and networks, a folder named "data" will be created 
- **Input DTM Folder**: Folder containing all DTM
- **Sample Distance**: The distance at which to split the edges of the network to calculate their slope and travel time. The selection of this variable determines the slope detail in the network and should be based on some tradeoff between your desired network slope resolution and the resolution of the DTM, as this can dramatically increase the number of edges in your network. In [Higgins (2019)](https://doi.org/10.1016/j.landurbplan.2018.12.011) for example, a sample distance of 10m was determined to be a reasonable compromise with a DTM available at a 2m resolution. Short of Network Analyst continuously differentiating over network segments to find their slope (which it cannot do), splitting up longer lines into smaller segments to calculate their average slope is an effective compromise for implementing slope-based travel times into the networks.
- Network has **No Split** edges (*optional*): If checked, this parameter indicates that your input 2D network has lines that should not be split by the tool. Useful for line features like bridges, where the standard interpolation and line splitting work flow could result in these edges traversing up and down the steep sides of a ravine in the DTM.
  - *NO_SPLIT*: A field in the pedestrian network that takes a value of 1 for any edges that will not be split by the tool. If you would like to use the No Split option, the tool is presently **hard coded** to expect a field *NO_SPLIT* in the input 2D network. With NO_SPLIT = 1, these edges will have the height of their start and end point coordinates interpolated from the DTM, but will not be split further. Slope, and slope-aware travel times will still be calculated based on the average slope of the unsplit line’s start and end points in 3D space. If you tick the *No Split* box but do not have any *NO_SPLIT* links identified, the tool will not work properly. We will try to make this more user-friendly in a future release.
- Network as **No Slope** edges (*optional*): If checked, this parameter indicates that your input 2D network has edges that should not have their travel time based on the slope of the terrain. Useful for any network elements that you do not want to have 3D, slope-aware travel times, such as internal pathways in buildings or pedestrian subways. If slope were applied, would result in inaccurate estimates of travel time.
  - *NO_SLOPE*: A field in the pedestrian network that takes a value of 1 for any edges for which their travel time will be based on an assumed flat plane.  If you would like to use the No Split option, the tool is presently **hard coded** to expect a field *NO_SLOPE* in the input 2D network. With NO_SLOPE = 1, these edges still have their height interpolated from the DTM, but these values are not used to calculate their travel time; the 2D travel time is used instead. This is done to maintain network topology when creating a network that uses the geometry of features for elevation in Network Analyst.
- **New 3D Network Output Folder**: The folder to output 3D pedestrian network for further analysis. The networks each has the following new fields:  

### Script Outputs
- **3D Pedestrian Networks**: Each 3D pedestrian network is stored in the folder specified above for further analysis. The networks each has the following new fields:
  - *Start_Z*: Start point Z-coordinate of the line interpolated from the DTM, based on its original digitization direction.
  - *End_Z*: End point Z-coordinate of the line interpolated from the DTM, based on its original digitization direction.
  - *Max_Z*: Maximum height value of the line interpolated from the DTM.
  - *Length3D*: 3D length of the line.
  - *AvgSlope*: Absolute slope of the line.
  - *FT_MIN_2D*: Walk time in minutes to traverse the line segment in the From-To direction, based on the 2D length of the line and the flat-ground walking speed of about 5kph.
  - *TF_MIN_2D*: Walk time in minutes to traverse the line segment in the To-From direction, based on the 2D length of the line and the flat-ground walking speed of about 5kph.
  - *FT_MIN_3D*: Walk time in minutes to traverse the line segment in the From-To direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment ((*End_Z*-*Start_Z*)/2D length of the line).
  - *TF_MIN_3D*: Walk time in minutes to traverse the line segment in the To-From direction, based on the 3D length of the line and an assumed walking velocity based on the slope of the line segment ((*Start_Z*-*End_Z*)/2D length of the line).

#### Example Usage
<img width="500" alt="toolcapture_sample" src="/assets/img/toolcapture_sample.jpg">

## Creating your Network Dataset
With the tool complete, you can now make a 3D pedestrian network using Network Analyst in ArcGIS. In particular, users can model elevation using feature geometry and specify the **TravelTime_3D** (using the *FT_MIN_3D* and *TF_MIN_3D* fields) cost attribute in **minutes**. A second **TravelTime_2D** (using the *FT_MIN_2D* and *TF_MIN_2D* fields) cost attribute can be specified and compared with results from the **TravelTime_3D** cost attribute to reveal the estimated impact on pedestrian travel when taking slope into account.

## References

Boeing, G. (2017). OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks. *Computers, Environment and Urban Systems*, 65, 126-139. DOI: [10.1016/j.compenvurbsys.2017.05.004](https://doi.org/10.1016/j.compenvurbsys.2017.05.004)

Higgins, C. (2019). A 4D spatio-temporal approach to modelling land value uplift from rapid transit in high density and topographically-rich cities. *Landscape and Urban Planning*. *185*, 68-82. DOI: [10.1016/j.landurbplan.2018.12.011](https://doi.org/10.1016/j.landurbplan.2018.12.011)

Tobler, W. (1993). Three presentations on geographical analysis and modeling: Non-isotropic geographic modeling speculations on the geometry of geography global spatial analysis. *National center for geographic information and analysis*. 93(1).
