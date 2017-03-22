# -*- coding: utf-8 -*-
import nvdbapi
import nvdb2geojson
import json
"""
Kommandolinjeverktøy for import av NVDB vegnett og fagdata til QGIS
Bruker nvdb2geojson og mellomlagrer geojson som fil. 
Argumentet er nvdbapi.py er en av klasene nvdbVegnett eller nvdbFagdata
definert i nvdbapi.py

Før bruk må du sette områdefilter og evt egenskapsfilter
"""

def nvdb2qgis( nvdbklasse, lagnavn): 
    
    if isinstance( nvdbklasse, nvdbVegnett): 
        geojsondata = nvdb2geojson.vegnett2geojson( nvdbklasse)
        
    else: 
        print( "Ikke implementert!") 
        return 
    
    with open( 'nvdbtmp.geojson') as f: 
        json.dump( geojsondata, f)
        
    iface.addVectorLayer( 'nvdbtmp.geojson', lagnavn, 'ogr')
    
    