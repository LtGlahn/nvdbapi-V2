# -*- coding: utf-8 -*-
"""Lagre vegnett og fagdata fra NVDB til geojson. 
Bruker klassene nvdbVegnett og nvdbFagdata fra nvdbapi.py

Pga shapely-biblioteket, som kan være litt trælete å installere, har jeg 
valgt å skille lagring til geojson fra resten. 

""" 
import nvdbapi
import geojson 
import json 
import copy
import shapely.wkt
from warnings import warn



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
    """Konverterer NVDB vegnett til dict med geojson - struktur, men med 
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

def fagdata2geojson( fagdata, ignorewarning=False, maxcount=False, vegsegmenter=True):
    """Konverterer NVDB fagdata til dict med geojson - struktur, men med 
    koordinater i UTM sone 33 (epsg:25833). Dette er ikke standard 
    geojson lenger, men vi angir det likevel i header. 
    
    
    Du kan også bruke flagget maxcount=<tall> for å laste ned inntil et 
    visst antall vegobjekter. 
    
    Mange vegobjekter er stedfestet på mer enn en veglenke/veglenkedel. I NVDB
    API er dette synlig ved at objektet går over mer enn ett vegsegment
    (ved å føye til parameter &inkluder=vegsegmenter i spørringen). Disse 
    objektene vil typisk ha en MULTILINESTRING-geometri, satt sammen av 
    LINESTRING-verdiene fra alle vegsegmentene. 
    
    I slike tilfeller velger vi å opprette en unik geojson-feature per vegsegment. 
    NVDB ID og egenskapsverdier blir like, og i tillegg numererer vi segmentene 
    og oppgir hvor mange segmenter som inngår i det opprinnelige NVDB-fagobjektet. 
    
    Fordeler
        * Unike vegreferanser per geojson-feature(vegnummer, hp og meterverdier)
        * Unike veglenke-ID og veglenkeposisjon per geojson-feature
        * Ingen MULTILINESTRING-geometri 
        
    Ulemper
        * Mister informasjon om egengeometri
        (vil bli valgbart i senere versjon)
    
    Eksempel
    f = ndbFagdata(105) # Fartsgrense
    f.addfilter_geo( { 'kommune' : 1601, 'vegreferanse' : 'Ev6' })
    gjson = fagdata2geojson( f) 
    """ 

    mygeojson = geojsontemplate()
    
            
    
    v = fagdata.nesteForekomst()
    count = 0
    stopp = False
    while v and not stopp:
        
        
        # Egenskapsverdier
        egenskaper = {}        
        for k in v['egenskaper']:
            egenskaper[k['navn']] = k['verdi']

        egenskaper['id'] = v['id']
        egenskaper['metadata'] = v['metadata']


            
        if vegsegmenter: 
        
            # En ny feature per vegsegment 
            egenskaper['antall vegsegmenter'] = len( v['vegsegmenter'])
            count = 0
            for seg in v['vegsegmenter']: 
                eg = copy.deepcopy( egenskaper )
                count += 1
                eg['vegsegment nr'] = count
                
                geom = shapely.wkt.loads( seg['geometri']['wkt'])
                
                seg.pop('geometri')
                vref = seg.pop( 'vegreferanse')
                eg.update( vref)
                eg.update(seg)
                
                mygeojson['features'].append( geojson.Feature(geometry=geom, 
                                                              properties=eg))

        else: 
            geom = shapely.wkt.loads( v['geometri']['wkt']  )
            v['lokasjon'].pop('geometri')
            egenskaper['lokasjon'] = v['lokasjon']
            mygeojson['features'].append( geojson.Feature(geometry=geom, 
                                                              properties=egenskaper))

        
        count += 1
        if maxcount and count >= maxcount: 
            stopp = True 
        v = fagdata.nesteForekomst()

    return mygeojson    


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
    