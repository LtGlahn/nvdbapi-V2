# -*- coding: utf-8 -*-
"""Lagre vegnett og fagdata fra NVDB til geojson. 
Bruker klassene nvdbVegnett og nvdbFagdata fra nvdbapi.py

Pga shapely-biblioteket, som kan være litt trælete å installere, har jeg 
valgt å skille lagring til geojson fra resten. 

""" 
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


def vegnett2geojson(vegnett, ignorewarning=False, maxcount=False):
    """Konverterer vegnett til dict med geojson - struktur, men med 
    koordinater i UTM sone 33 (epsg:25833). Dette er ikke standard 
    geojson lenger, men vi angir det likevel i header. 
    
    Funksjonen krever at du bruker områdefilter (geofilter), som settes med
    funksjon addfilter_geo()
    Uten områdefilter skulle bety at du laster ned data for hele landet 
    Derfor returneres en advarsel pluss de lenkene som er i 
    pagineringsbufferet  (typisk 1000). Dette kan overstyres med 
    flagget ignorewarning=True. 
    
    Du kan også bruke flagget maxcount=100000 for å laste ned inntil et 
    visst antal veglenker. 
    
    Eksempel
    v = nvdbVegnett()
    v.addfilter_geo( { 'kommune' : 1601, 'vegreferanse' : 'Ev6' })
    gjson = v.vegnett2geojson) 
    """ 
    if not vegnett.geofilter and not ignorewarning and not maxcount: 
        warn( 'For mange lenker - bruk  ignorewarning=True for hele Norge' ) 
        maxcount = 1000
        
    
    mygeojson = geojsontemplate()
    
            
    
    v = vegnett.nesteForekomst()
    count = 0
    stopp = False
    while v and not stopp:
        
        egenskaper = {}
        wktgeom = v['geometri'].pop( 'wkt')
        for k in v.keys():
            egenskaper[k] = v[k]

        geom = shapely.wkt.loads( wktgeom)
        
        
        mygeojson['features'].append( geojson.Feature(geometry=geom, 
                                                      properties=egenskaper))
        
        
        count += 1
        if maxcount and count >= maxcount: 
            stopp = True 
        v = vegnett.nesteForekomst()

    return mygeojson

def fagdata2geojson( fagdata, maxcount=False): 
    
    
def geojsontemplate():
    return {
                    "type": "FeatureCollection",
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "urn:ogc:def:crs:EPSG::25833"
                        }
                    },
                    "features": []
                }
    