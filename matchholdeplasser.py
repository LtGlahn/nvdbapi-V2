# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 14:52:55 2018

@author: jajens
"""

# Builtin libraries
import json
import math

# Well known 3rd party librariers
import requests 
import pandas as pd
import pyproj
import numpy as np

# My libraries
import nvdbapi
import bomstasjoner_retninger as bom


def finnveg( lon, lat): 
    """
    Finner nærmeste vanlige veg til koordinatene (lon, lat). 
    
    Vegstatus er V (vanlig veg) eller T (midlertidig status bilveg)
    """
    
    headers = {'X-Client': 'nvdbapi.py fra Nvdb gjengen, vegdirektoratet',
             'X-Kontaktperson': 'jan.kristian.jensen@vegvesen.no',
             'accept': 'application/vnd.vegvesen.nvdb-v2+json'}
    
    apiurl = 'https://www.vegvesen.no/nvdb/api/v2/posisjon'
    params = { 'lat' : lat, 'lon' : lon, 'vegreferanse' : ['EV', 'FV', 'RV', 
                    'KV', 'PV', 'SV', 'ET', 'FT', 'RT', 'KT', 'PT', 'ST']}
    r = requests.get( apiurl, params=params, headers=headers )
    return r.json()


def reprojiser( lon, lat): 
    """
    Re-projiserer lon,lat => utm33
    """
    crs_wgs = pyproj.Proj(init='epsg:4326') # assuming you're using WGS84 geographic
    crs_utm = pyproj.Proj(init='epsg:25833' )
    x, y = pyproj.transform( crs_wgs, crs_utm, lon, lat )
    return (x, y)

def points2dir( x0, y0, x1, y1):
    sig = math.atan2( x1-x0, y1-y0 )
    if sig < 0: 
        sig += 2* math.pi
        
    return sig * 180 / math.pi
    

def ang2vec( compassdirection, X=0, Y=0):
    """
    Beregner vektorkomponent (x2, y2) i vektoren (0, 0) => (x2, y2) ut fra kompassretning
    """
    cm = compassdirection * math.pi / 180
    x2 = math.sin( cm) + X
    y2 = math.cos( cm) + Y
    
    
    return (x2, y2)

def isleftrigth( Xside, Yside, Xveg, Yveg, roadDirection, minimumdist=0.5, 
                                                minimumangle=30, debug=False): 
    """
    Regner ut om et punkt ligger til høyre eller venstre for senterlinja 
    når du oppgir koordinater for punktet og senterlinja, samt 
    metreringsretningen i grader. 
           
    Arguments: 
        Xside, Yside, Xveg, Yveg =  Koordinater for punkt i sideterreng
                                    og senterlinje
        roadDirection = Kompasslinje for metreringsretning på senterlinje. 

    Keywords:
        minimumdist=0.5 Minimumsavstand senterlinje-punkt til side for vegen
        minimangle=30   Minimum vinkel mellom vektorene, i grader. 
        debug=False     Skriver detaljert info 
    
    Returns
        Tekststreng "LEFT" eller "RIGHT", evt None om kvalitetssjekkene feiler
    
    """
    
    (Xd1, Yd1) = ang2vec( roadDirection, X=Xveg, Y=Yveg) 
    
    vec1 = [Xquay-Xveg,Yquay-Yveg]
    vec2 = [Xd1-Xveg, Yd1-Yveg]
    dist = np.linalg.norm( vec1)
    if dist < minimumdist: 
        if debug: 
            print( "Avstand", dist, " < minimumsavstand", minimumdist)
        return None 
    
    angle = np.math.atan2(np.linalg.det([vec1,vec2]),np.dot(vec1,vec2))
    if abs( np.degrees(angle)) < abs(minimumangle): 
        if debug: 
            print( "Vinkelforskjell", abs(np.degrees(angle)), " < minimumsvinkel ", minimumangle)
        return None
    
    cx = np.cross( vec1, vec2  ).tolist()
    
    
    if debug: 
        print( "Vektor kai-veg", vec1)
        print( "vektor langs veg", vec2)
        print( "Avstand kant-veg", dist)
        print( "Vinkel", np.degrees( angle))
        print( "Kryssprodukt", cx)
    
    
    # 0.5 tilsvarer 30 graders vinkel ved 1 m avstand veg-quay, 
    # evt cirka 15 grader ved 2 m avstand
    # eller 0.5 m avstand ved 90 grader
    if cx > 0: 
        return "RIGHT"
    elif cx < 0: 
        return "LEFT"
    else: 
        return None
    
if __name__ == "__main__": 
    
    
    filnavn = '../data/rb_norway-aggregated-gtfs-basic/stops.txt'    
    enturdata = pd.DataFrame.from_csv( filnavn )
    
    
