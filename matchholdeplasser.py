# -*- coding: utf-8 -*-
"""
Created on Wed Oct  3 14:52:55 2018

@author: jajens
"""

# Builtin libraries
import json
import math
import datetime
from time import sleep

# Well known 3rd party librariers
import requests 
import pandas as pd
import pyproj
import numpy as np
import shapely.wkt as shpwkt
from xml.parsers.expat import ExpatError

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
    Regner fra kompassretning til vektor-koordinater 
    
    Arguments
        compassdirection | float Kompassretning i grader
        
    Keywords
        X=0, Y=0 float Koordinater i kartesisk koordinatsystem. 
        
    Returns 
        (x2, y2) float Siste koordinatpar i vektoren (X, Y) => (x2, y2) 
            hvor vektoren peker i kompassretning og har lengde 1
                 
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
    
    vec1 = [Xside-Xveg,Yside-Yveg]
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
    
def hentkompassretning( veglenkeid, posisjon, delay=0): 
    """
    Rekursiv wrapper rundt bomstasjoner_retninger.kompassetning
    
    Vil prøve igjen og igjen rekursinvt inntil vi får kontakt
    
    
    """

    try:         
            (vegnettretn, metreringsretn) = bom.kompassretning( veglenkeid, posisjon)
            
    except requests.exceptions.ConnectionError: 
        delay += 30
        print( "Nettverksfeil Visveginfo, prøver igjen etter ..." , delay, "sekunder")
        sleep(delay)
        (vegnettretn, metreringsretn) = hentkompassretning( veglenkeid, posisjon, delay=delay)
        
    except ExpatError: 
        vegnettretn = None
        metreringsretn = None

    return vegnettretn, metreringsretn


def wrap_finnveg( lon, lat, delay=0):
    """
    Rekursiv wrappper rundt finnveg-funksjon, gir ikke opp ved nettverksfeil
    
    Prøver igjen inntil det funker 
    """
    try:
        veg = finnveg( lon, lat) 

    except requests.exceptions.ConnectionError: 
        delay += 15 
        print( "Nettverksfeil NVDB api, prøver igjen etter ", delay, "sekunder" )
        sleep(delay)
        veg = wrap_finnveg( lon, lat, delay=delay) 
    
    return veg    
    
if __name__ == "__main__": 
    
    
    filnavn = '../data/rb_norway-aggregated-gtfs-basic/stops.txt'    
    enturdata = pd.read_csv( filnavn )
    
    enturdata['veg_avstand'] = np.nan
    enturdata['vegreferanse'] = ''
    enturdata['veglenkepos'] = ''
    enturdata['vegkategori'] = ''
    enturdata['vegnummer'] = np.nan
    enturdata['side'] = ''
    enturdata['metreringsretn'] = np.nan
    enturdata['vegnettretn'] = np.nan

    # iterer med get_value / set_value ref
    # https://medium.com/@rtjeannier/pandas-101-cont-9d061cb73bfc
    count = 0
    t0 = datetime.datetime.now()
    
    for i in enturdata.index: 
        # i = enturdata.index[0]
    
        count += 1
        if count % 1000 == 0 or count == 10 or count == 100: 
            dt = datetime.datetime.now() - t0
            
            print( f'Holdeplass {count} av {len(enturdata)}'\
                  f' etter {dt.total_seconds()/60:.2f} minutt')
        
        if 'NSR:Quay' in enturdata.get_value( i, 'stop_id'): 
            lon = enturdata.get_value( i, 'stop_lon')
            lat = enturdata.get_value( i, 'stop_lat')
            (xstop, ystop) = reprojiser( lon, lat)
            veg = wrap_finnveg( lon, lat) 
    
             
            if not 'code' in veg[0].keys(): 
            
                vegpos = shpwkt.loads( veg[0]['geometri']['wkt'])
                
                junk = enturdata.set_value( i, 'veg_avstand', veg[0]['avstand'])
                junk = enturdata.set_value( i, 'vegreferanse', veg[0]['vegreferanse']['kortform'])
                junk = enturdata.set_value( i, 'veglenkepos', veg[0]['veglenke']['kortform'])
                junk = enturdata.set_value( i, 'vegkategori', veg[0]['vegreferanse']['kategori'])
                junk = enturdata.set_value( i, 'vegnummer', veg[0]['vegreferanse']['nummer'])
            
                (vegnettretn, metreringsretn) = hentkompassretning(
                        veg[0]['veglenke']['id'], veg[0]['veglenke']['posisjon'])
                    
                
                if metreringsretn: 
                    side = isleftrigth( xstop, ystop, vegpos.x, vegpos.y, metreringsretn )                  
                 
                    junk = enturdata.set_value( i, 'side', side)
                    junk = enturdata.set_value( i, 'metreringsretn', metreringsretn)
                    junk = enturdata.set_value( i, 'vegnettretn', vegnettretn)
            

    enturdata.to_csv( 'holdeplasser_medveg.csv', index=False)
    t1 = datetime.datetime.now()
