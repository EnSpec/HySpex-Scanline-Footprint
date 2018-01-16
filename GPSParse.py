#!/usr/bin/env python3
import numpy as np
import requests
import shapefile
import os
import sys
from matplotlib import pyplot as plt

EARTH_RADIUS = 6.3710088e6 #meters

def toPoly(coords,elev,fname):
    """Save a lat,lon coordinate dictionary to a shapefile"""
    polyw = shapefile.Writer(shapefile.POLYGON)
    polyw.field('idx','N',10)
    bounds = [list(map(lambda c:[c['lon'],c['lat'],elev],coords))]
    polyw.poly(parts=bounds)
    polyw.record('0','Scanline Bounds')
    polyw.save(fname)

def atDistAndBearing(start,dist,bearing):
    """Find the destination from coordinates start travelling 
    dist meters at bearing bearing
    """
    lat0 = start['lat']
    lon0 = start['lon']
    latr0 = np.deg2rad(lat0)
    lonr0 = np.deg2rad(lon0)
    bearingr = np.deg2rad(bearing)
    d_div_R = dist/EARTH_RADIUS
    latrf = np.arcsin(np.sin(latr0)*np.cos(d_div_R)+
                np.cos(latr0)*np.sin(d_div_R)*np.cos(bearingr))

    lonrf = np.arctan2(np.sin(bearingr)*np.sin(d_div_R)*np.cos(latr0),
                np.cos(d_div_R)-np.sin(latr0)*np.sin(latrf)) + lonr0

    latf = np.rad2deg(latrf)
    lonf = ((np.rad2deg(lonrf)+540)%360) - 180
    return {'lat':latf,'lon':lonf}

def getGoogleElevation(coords,keyfile="key.txt"):
    print("Using Google API to get elevation.")
    try:
        KEY = open(keyfile,'r').read().strip()
    except FileNotFoundError:
        print("Google API key not found at %s.\n"
              "Use the --key-file argument to"
              " specify the location of your API key (default key.txt)"%keyfile)
        exit(1)

    API_URL = 'https://maps.googleapis.com/maps/api/elevation/json' 
    locs = '|'.join(['{lat},{lon}'.format(**c)for c in coords])
    params = {'key':KEY,'locations':locs}
    r = requests.get(API_URL,params=params)
    return [p['elevation'] for p in r.json()['results']]


def findGroundLocation(coord,alt,pitch,yaw):
    dY = alt*np.tan(np.deg2rad(pitch))
    location = atDistAndBearing(coord,dY,yaw)
    return location

def getScanEdges(coord,alt,roll,pitch,yaw,view_angl=17):
    ground_pos = findGroundLocation(coord,alt,pitch,yaw)
    thetaL = np.deg2rad(view_angl/2+roll)
    thetaR = np.deg2rad(view_angl/2-roll)
    dXl = alt*np.tan(thetaL)
    dXr = alt*np.tan(thetaR)
    lBound = atDistAndBearing(ground_pos,dXl,yaw-90)
    rBound = atDistAndBearing(ground_pos,dXr,yaw+90)
    return lBound,rBound

LOG_HEADER="ImgName,CtrLon,CtrLat,GndDEMm,SensorMSLm,SensorAGLm,ImgFOV"
def logMeta(log_fname,coord,gps_fname,ground_elev,alt_msl,fov):
    im_fname = os.path.basename(gps_fname).replace('_raw.txt','')
    alt_agl = alt_msl - ground_elev
    print(LOG_HEADER)
    meta_list = [im_fname,coord['lon'],coord['lat'],ground_elev,alt_msl,fov]
    meta_str = ",".join(map(str,meta_list))
    print(meta_str+"\n")
    if os.path.exists(log_fname):
        with open(log_fname,"a") as f:
            f.write(meta_str+'\n')
    else:
        with open(log_fname,"w") as f:
            f.write(LOG_HEADER+'\n')
            f.write(meta_str+'\n')


def processGPS(config):
    view_angl = config.fov
    data = np.loadtxt(config.gps_file)
    lSide = []
    rSide = []
    elevation = config.elev
    if elevation is None:
        #get elevations from the google elevation api
        ctrs = np.linspace(0,data.shape[0],config.npoints+2,dtype=int)[1:-1]
        locs = [{'lat':data[i,2],'lon':data[i,1]}for i in ctrs]
        midpt_elevs = getGoogleElevation(locs,config.keyfile)
        elevation = np.interp(np.arange(data.shape[0]),ctrs,midpt_elevs)
    else:
        elevation = np.zeros(data.shape[0])+elevation
    for i,(lon,lat,alt,roll,pitch,yaw) in enumerate(data[:,1:-1]):
        alt -= elevation[i]
        if config.smooth:
            roll = 0
        lBound,rBound = getScanEdges({'lat':lat,'lon':lon},alt,roll,pitch,yaw,view_angl)
        lSide.append(lBound)
        rSide.append(rBound)
        if config.log_meta and i==int(data.shape[0]/2):
            #log the midpoint of the scan as metadata
            img_ctr = findGroundLocation({'lat':lat,'lon':lon},alt,pitch,yaw)
            logMeta(config.log_meta,img_ctr,config.gps_file,np.mean(elevation),
                    alt,view_angl)

    out = config.out or os.path.split(config.gps_file)[1].replace('.txt','')
    toPoly(lSide+rSide[::-1],np.mean(elevation),out)



IN_HELP="""
Input file of tab-separated gps coordinates. 
File Format: lon lat alt roll pitch yaw
"""
OUT_HELP="""
Name of shapefile to write (default <input_gps>.shp)
"""
FOV_HELP="""
Field of view of spectrometer being used (default 17 degrees)
"""
GOOGL_HELP="""
Number of elevation points to request from the Google API (default 1). 
Elevations are interpolated evenly throughout the scan area.
Note: Requires a google API key (see --key-file)
"""
KEY_HELP="""
Location of file containing Google API key to use for Google Maps elevation 
requests. If not specified, program will try to read ./key.txt 
"""
ELEV_HELP="""
Use a single elevation value (in meters) for the whole reading instead of
using the google elevation api
"""
SMOOTH_HELP="""Produce a shapefile with fewer jagged edges"""

LOG_HELP="""
Append metadata to a log file. Creates the log file if it doesn't exist
"""

if __name__ =='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
            "Convert gps text file to shapefile")
    parser.add_argument("gps_file",help=IN_HELP)
    parser.add_argument("-o","--out",help=OUT_HELP)
    parser.add_argument("-v","--fov",type=float,default=17,help=FOV_HELP)
    parser.add_argument("-g","--google-elev",metavar="NPOINTS",dest="npoints",
            type=int,default=1,help=GOOGL_HELP)    
    parser.add_argument("-k","--key-file",metavar="KEY_FILE",dest="keyfile",
            type=str,help=KEY_HELP,default="key.txt")
    parser.add_argument("-e","--elev",type=int,help=ELEV_HELP)
    parser.add_argument("-s","--smooth",help=SMOOTH_HELP,action='store_true')
    parser.add_argument("-l","--log-meta",metavar="LOG_FILE",help=LOG_HELP)
    args = parser.parse_args()
    processGPS(args)

