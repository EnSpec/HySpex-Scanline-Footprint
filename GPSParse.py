import numpy as np
import LonLatMath as llmath
import requests
import SHPParse

KEY = open(".secret/key.txt",'r').read().strip()

def getElevation(coord):
    #don't want to use API too much right off the bat
    return 186
    API_URL = 'https://maps.googleapis.com/maps/api/elevation/json' 
    params = {'key':KEY,'locations':'{lat},{lon}'.format(**coord)}
    r = requests.get(API_URL,params=params)
    return r.json()['results'][0]['elevation']


def findGroundLocation(coord,alt,pitch,yaw):
    dY = alt*np.tan(np.deg2rad(-pitch))
    location = llmath.atDistAndBearing(coord,dY,yaw)
    return location

def getScanEdges(coord,alt,roll,pitch,yaw,view_angl=17):
    ground_pos = findGroundLocation(coord,alt,pitch,yaw)
    thetaL = np.deg2rad(view_angl+roll)
    thetaR = np.deg2rad(view_angl-roll)
    dXl = alt*np.tan(np.deg2rad(thetaL))
    dXr = alt*np.tan(np.deg2rad(thetaR))
    lBound = llmath.atDistAndBearing(ground_pos,dXl,yaw+90)
    rBound = llmath.atDistAndBearing(ground_pos,dXl,yaw-90)
    return lBound,rBound


def processGPS(gps_file,out_shapefile='out',view_angl=17):
    view_angl = float(view_angl)
    data = np.loadtxt(gps_file)
    lSide = []
    rSide = []
    elevation = getElevation({'lat':data[0,1],'lon':data[0,0]})
    for lon,lat,alt,roll,pitch,yaw in data[:,1:-1]:
        alt -= elevation
        lBound,rBound = getScanEdges({'lat':lat,'lon':lon},alt,roll,pitch,yaw)
        lSide.append(lBound)
        rSide.append(rBound)

    SHPParse.toPoly(lSide+rSide[::-1],elevation,out_shapefile)


if __name__ =='__main__':
    import sys
    processGPS(*sys.argv[1:])
