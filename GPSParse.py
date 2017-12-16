#!/usr/bin/env python3
import numpy as np
import LonLatMath as llmath
import requests
import SHPParse

KEY = open("key.txt",'r').read().strip()

def getElevation(coord):
    print("Using Google API to get elevation.")
    API_URL = 'https://maps.googleapis.com/maps/api/elevation/json' 
    params = {'key':KEY,'locations':'{lat},{lon}'.format(**coord)}
    r = requests.get(API_URL,params=params)
    return r.json()['results'][0]['elevation']


def findGroundLocation(coord,alt,pitch,yaw):
    dY = alt*np.tan(np.deg2rad(pitch))
    location = llmath.atDistAndBearing(coord,dY,yaw)
    return location

def getScanEdges(coord,alt,roll,pitch,yaw,view_angl=17):
    ground_pos = findGroundLocation(coord,alt,pitch,yaw)
    thetaL = np.deg2rad(view_angl/2+roll)
    thetaR = np.deg2rad(view_angl/2-roll)
    dXl = alt*np.tan(thetaL)
    dXr = alt*np.tan(thetaR)
    lBound = llmath.atDistAndBearing(ground_pos,dXl,yaw-90)
    rBound = llmath.atDistAndBearing(ground_pos,dXr,yaw+90)
    return lBound,rBound


def processGPS(gps_file,out_shapefile='out',view_angl=17,elevation =None):
    view_angl = float(view_angl)
    data = np.loadtxt(gps_file)
    lSide = []
    rSide = []
    if elevation is None:
        elevation = getElevation({'lat':data[0,2],'lon':data[0,1]})
    else:
        elevation = float(elevation)
    for i,(lon,lat,alt,roll,pitch,yaw) in enumerate(data[:,1:-1]):
        alt -= elevation
        lBound,rBound = getScanEdges({'lat':lat,'lon':lon},alt,roll,pitch,yaw,view_angl)
        lSide.append(lBound)
        rSide.append(rBound)

    SHPParse.toPoly(lSide+rSide[::-1],elevation,out_shapefile)


#pip install requests
#pip install pyshp
#python GPSParse.py input_gps.txt output.shp [optional: view_angle elevation]
if __name__ =='__main__':
    import sys
    #more command line:
    #give elevation
    #coarse view
    processGPS(*sys.argv[1:])
