# -*- coding: utf-8 -*-
from nvdbapi import * 
import nvdb2geojson
import json
from qgis.core import * 

"""
Kommandolinjeverktøy for import av NVDB vegnett og fagdata til QGIS
Bruker nvdb2geojson og mellomlagrer geojson som fil. 
Argumentet er nvdbapi.py er en av klasene nvdbVegnett eller nvdbFagdata
definert i nvdbapi.py

Før bruk må du sette områdefilter og evt egenskapsfilter
"""

def nvdb2qgislag(nvdbklasse, lagnavn, iface, **kwargs): 
    
    if isinstance( nvdbklasse, nvdbFagdata):
        geojsondata = nvdb2geojson.fagdata2geojson( nvdbklasse, **kwargs)
    elif isinstance( nvdbklasse, nvdbVegnett): 
        geojsondata = nvdb2geojson.vegnett2geojson( nvdbklasse, **kwargs)
    else: 
        print( "Ikke implementert!") 
        return 
    
    tmp = json.dumps( geojsondata )        
    iface.addVectorLayer( tmp, lagnavn, 'ogr')
    
    