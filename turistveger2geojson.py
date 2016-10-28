# -*- coding: utf-8 -*-

import nvdbapi
import geojson 
import json 
import shapely.wkt
# How to install shapely on windows: 
# http://deparkes.co.uk/2015/01/29/install-shapely-on-anaconda/ 
# This also works for other python distributions than anaconda! 
# 
# As described Just go to the "wheel download page" 
# http://www.lfd.uci.edu/~gohlke/pythonlibs/#shapely
# download the appropriate wheel for your python version and platform
# (python 2.x or 3.x, 32 or 64 bit architecture of your PYTHON INSTALLATION
# (on 64 bit machines you may choose 32 or 64 bit installations of python , 
# so beware))

def reverseShapelyCoords_dropZ(shapelygeom): 
    """
    Reverses the axis order (X,Y => Y,X) and drops the Z coordinate
    from input shapely geometry object
    """
    
    if type(shapelygeom) == 'shapely.geometry.multilinestring.MultiLineString':
        pass


turistveger = nvdbapi.nvdbFagdata(777)
turistveger.respons['srid'] = 4326 # lat/lon coordinates

myGeojson = { "type": "FeatureCollection",
    "features": []
}


turistveg1 = turistveger.nesteNvdbFagObjekt() 


while turistveg1: 
    egenskaper = {  'navn' : turistveg1.egenskapverdi('Navn'), 
                      'linkturistveg' : turistveg1.egenskapverdi('Link turistveg'), 
                    'status' : turistveg1.egenskapverdi('Status')
                }
    geom = shapely.wkt.loads( turistveg1.wkt()) 
    mygeo =  geojson.Feature(geometry=geom, properties=egenskaper) 
    myGeojson['features'].append( mygeo) 
    turistveg1 = turistveger.nesteNvdbFagObjekt()
    

# python 3 syntax 
# For python 2.7 see http://stackoverflow.com/a/14870531 
with open( 'turistveger.geojson', 'w', encoding='utf-8' ) as fh:
    json.dump(myGeojson, fh, ensure_ascii=False, indent=4 )

# WARNING
# This example produces 3D geometry (right now). Trying to fix that
# The geometry could also do very well with some thinning.  