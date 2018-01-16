#!/usr/bin/env python3
import numpy as np
import requests
import shapefile

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
    `dist` meters at bearing `bearing`
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

def getGoogleElevation(coord):
    print("Using Google API to get elevation.")
    try:
        KEY = open("key.txt",'r').read().strip()
    except FileNotFoundError:
        print("Google API key not found. Please enter an API key:")
        KEY = input()
        with open("key.txt",'w') as f:
            f.write(KEY)

    API_URL = 'https://maps.googleapis.com/maps/api/elevation/json' 
    params = {'key':KEY,'locations':'{lat},{lon}'.format(**coord)}
    r = requests.get(API_URL,params=params)
    return r.json()['results'][0]['elevation']


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


def processGPS(gps_file,out_shapefile='out',view_angl=17,elevation =None):
    view_angl = float(view_angl)
    data = np.loadtxt(gps_file)
    lSide = []
    rSide = []
    if elevation is None:
        elevation = getGoogleElevation({'lat':data[0,2],'lon':data[0,1]})
    else:
        elevation = float(elevation)
    for i,(lon,lat,alt,roll,pitch,yaw) in enumerate(data[:,1:-1]):
        alt -= elevation
        lBound,rBound = getScanEdges({'lat':lat,'lon':lon},alt,roll,pitch,yaw,view_angl)
        lSide.append(lBound)
        rSide.append(rBound)

    toPoly(lSide+rSide[::-1],elevation,out_shapefile)


#pip install requests
#pip install pyshp
#python GPSParse.py input_gps.txt output.shp [optional: view_angle elevation]
IN_HELP="""
input file of tab-separated gps coordinates. 
Format: lon lat alt roll pitch yaw
"""
GOOGL_HELP="""
Number of elevation points to request from the Google API (default 1). 
Elevations are interpolated evenly throughout the scan area.
Note: Requires a google API key.
"""
ELEV_HELP="""
Use a single elevation value (in meters) for the whole reading instead of
using the google elevation api.
"""
EFILE_HELP="""
Read a list of elevations from a file instead of using the google elevation api.
Elevations are interpolated to the closest given value.
Format: lon lat elev.
"""

if __name__ =='__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
            "Convert gps text file to shapefile")
    parser.add_argument("gps_file",help=IN_HELP)
    parser.add_argument("--google-elev-points",help=GOOGL_HELP)    
    parser.add_argument("--elev")
    #more command line:
    #give elevation
    #coarse view
    processGPS(*sys.argv[1:])
