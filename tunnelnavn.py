# -*- coding: utf-8 -*-
"""Henter bruer fra NVDB og sjekker om navnet på brua finnes i Sentralt 
    stedsnavnregister (SSR). Lagrer treffliste til CSV-fil""" 

import nvdbapi
import xmltodict
import requests
import json
from shapely.wkt import loads as loadswkt  
# import pdb
import re
import pyproj  
from collections import OrderedDict


def askSSR( navn, bbox, debug=False): 
    """Slår opp i SSR på strengen navn. Wildcard-søk er støttet, ref
    SSR-dokumentasjonen. bbox er en shapely boundingBox-element, dvs en 
    liste med 4 koordinater (nedre venstre øst/nord og øvre høyre øst/nord)
    
    Plukker ut et koordinatpunkt og legger inn som E, N i UTM sone 32
    (epsg:25832)"""
    
    
    url = 'https://ws.geonorge.no/SKWS3Index/ssr/sok'
    params = {  'maxAnt' : '50', 
        'navn' : navn + '*', 
        'ostLL'     : bbox[0],
        'nordLL'    : bbox[1],
        'ostUR'     : bbox[2], 
        'nordUR'    : bbox[3]
        }
    r = requests.get( url, params=params)
    
    if debug: 
        print( navn, r.url)
    
    if not r.ok: 
        raise ImportError( "Kan ikke hente data fra SSR: %s" % r.url ) 
    else: 

        document =  xmltodict.parse( r.text )
        antGodeTreff = 0
        antSSRtreff = int( document['sokRes']['totaltAntallTreff'] )
        
        if  antSSRtreff == 0: 
            pass
            # Mer liberale oppslag mot 
        elif antSSRtreff == 1: 
            if sjekkNavn( document['sokRes']['stedsnavn']): 
                antGodeTreff = 1
            
        else: 
            for elem in document['sokRes']['stedsnavn']: 
                if sjekkNavn( elem ):
                    antGodeTreff += 1
                
        return antGodeTreff

def sjekkNavn( stedsnavn): 
    """Sjekker om stedsnavn-elementet fra SSR er det vi  vil ha"""

    godstatus = [ u'Vedtatt', u'Godkjent', u'Samlevedtak' ]

    if stedsnavn['navnetype'] == u'Bru' and \
        stedsnavn['skrivemaatestatus'] in godstatus: 
        
        return True
    
    else: 
        return False

def hentNvdbTunnel( debug = False):
    
    tunneller = nvdbapi.nvdbFagdata(581)
    tunneller.addfilter_egenskap('5225!=null' )



    if debug: 
        pass        
    
     
    header = [ 'Fylke', 'NVDBnavn', 'Lengde skiltet', 'E', 'N', 'NvdbId', 'Kommune', 'Match', 'SSRurl',  ]
    resultat = []
    resultat.append(header)
    tunn = tunneller.nesteNvdbFagObjekt()
    while tunn: 

        
        tunndata = OrderedDict()
        tunndata['Navn'] = tunn.egenskapverdi( 5225)
        if not tunn.egenskapverdi(5225):
            print( tunn.id, "Mangler navn")
        
        tunndata['skiltLen'] = tunn.egenskapverdi(8945, empty=0 )
        
        if not tunn.egenskapverdi( 8945):
            print( tunn.id, tunndata['Navn'], "Mangler skiltet lengde")
        
        # Finner tunnellbarn 
        if tunn.relasjoner: 
            for tunn2id in tunn.relasjoner['barn'][0]['vegobjekter']:
                tmp = tunneller.anrope('vegobjekter/67/' + 
                        str(tunn2id), parametre={"inkluder" : "alle"} ) 
                tunn2 = nvdbapi.nvdbFagdata( tmp )
            
        else: 
            print( tunn.id, tunndata['Navn'], "mangler tunnelløp")

        try:    
            geom = loadswkt( nvdbObj.geometri(geometritype='geometriUtm33'))
        except KeyError as e:
            print( "Ingen geometri", navn, nvdbObj.id )
            # Har noen bruer der vegen er lagt ned => intet lokasjonsobjekt 
            # i NVDB api'et. Trenger bedre håndtering av historikk... 
            
        else: 
            bbox = geom.buffer(1000).bounds
            pt = geom.centroid    
            ssrtreff = askSSR( brunavn3, bbox, debug=debug)         
            print( ssrtreff, "treff for", brunavn, 'lengde=', nvdbObj.egenskap(egenskapstype=1313) )
    
            if ssrtreff == 1:
                match = 'EKSAKT'
                navn2 = ''
                
            elif ssrtreff == 0:
                # Mer liberale søk i SSR 
                navn2 = brunavn3.rsplit(' ', 1)[0].strip() + '*'
                ssrtreff = askSSR( navn2, bbox) 
                
                print( "\t", ssrtreff, "treff for", navn2, 'lengde=', nvdbObj.egenskap(egenskapstype=1313) )
                
                if ssrtreff > 0: 
                    match = navn2
                else: 
                    match = 'INGEN'
    
            elif ssrtreff > 1: 
                
                match = 'FLERE?'
            
            # Reprojiserer, 
            utm33 = pyproj.Proj('+init=EPSG:25833')
            utm32 = pyproj.Proj('+init=EPSG:25832')
            x2,y2 = pyproj.transform(utm33, utm32, pt.x, pt.y) 
            
            liste = [ nvdbObj.data['lokasjon']['fylke']['nummer'], 
                        brunavn,
                        int(round( float( nvdbObj.egenskap(egenskapstype=1313)))) , # Lengde
                        int(round(x2)), int(round(y2)),                # Nord/øst koordiant
                        nvdbObj.id, match ]
            
            resultat.append( liste) 
            
        tunn = tunneller.nesteNvdbFagObjekt()

    return resultat
    nvdb.csv_skriv( 'brunavn.csv', resultat) 

if __name__ == '__main__': 
    
    print( "hello", "world")
    # resultat = hentNvdbTunnel( debug=False)
    
    # sluppen = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272765437') )
    # svin = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272299150') )

    # enkeltNvdbBru( sluppen) 
    # enkeltNvdbBru( svin) 
    
    
    
    


