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
import csv


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
        # raise ImportError( "Kan ikke hente data fra SSR: %s" % r.url ) 
        print( "SSR søk feiler", r.text)
        return( 0, r.url)
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
                
        return ( antGodeTreff, r.url)

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
    # tunneller.addfilter_geo( {'fylke' : 18 })
    # 


    if debug: 
        tunneller.addfilter_geo( {'kommune' : 1601 })
        
    resultat = []
    tunn = tunneller.nesteNvdbFagObjekt()
    while tunn: 

        if tunn.geometri: 
            tunndata = OrderedDict()
            tunndata['Kommune'] = tunn.lokasjon['kommuner'][0]
            tunndata['Navn'] = tunn.egenskapverdi( 5225)
            if not tunn.egenskapverdi(5225):
                print( tunn.id, "Mangler navn")
            
            tunndata['Skiltet lengde'] = tunn.egenskapverdi(8945 )
            
            if not tunn.egenskapverdi( 8945):
                print( tunn.id, tunndata['Navn'], "Mangler skiltet lengde")
            
            tunndata['Åpningsår'] = tunn.egenskapverdi( 10383 )
            # Finner tunnelløp som datterobjekt av tunnel
            tunnellop = tunn.relasjon( 67)
            
            tunnbarn_antall = 0
            tunnbarn_maksOppgittLengde = 0
            tunnbarn_maksFysiskLengde = 0
            tunnbarn_aapningsaar = 0
            if tunnellop: 
                tunnbarn_antall = len(tunnellop['vegobjekter'])
                for tunn2id in tunnellop['vegobjekter']:
                    try: 
                        tmp = tunneller.anrope('vegobjekter/67/' + 
                            str(tunn2id), parametre={"inkluder" : "alle"} ) 
                        
                    except ValueError: 
                        print( "finner ikke tunnelløp", tunn2id, "for",
                              tunn.id, tunndata['Navn'])
                    else: 
                        tunn2 = nvdbapi.nvdbFagObjekt( tmp )
                        
                        tunnbarn_maksOppgittLengde = max( tunn2.egenskapverdi( 
                                1317, empty=0), tunnbarn_maksOppgittLengde)
                        
                        tunnbarn_aapningsaar = min( tunnbarn_aapningsaar, 
                                        tunn2.egenskapverdi( 8356, empty=0))
                        
                        geom2 = loadswkt( tunn2.wkt())
                        tunnbarn_maksFysiskLengde = max( geom2.length, 
                                tunnbarn_maksFysiskLengde)
            else: 
                print( tunn.id, tunndata['Navn'], "mangler tunnelløp")
    
            tunndata['Antall Tunnelløp'] = tunnbarn_antall
            
            if tunnbarn_maksOppgittLengde == 0: 
                tunnbarn_maksOppgittLengde = None
                
            if tunnbarn_aapningsaar == 0: 
                tunnbarn_aapningsaar = None
            
            tunndata['Maks angitt lengde tunnelløp'] = tunnbarn_maksOppgittLengde
            tunndata['Maks fysisk lengde tunnelløp'] = tunnbarn_maksFysiskLengde
            tunndata['Åpningsår fra tunnelløp'] = tunnbarn_aapningsaar
       
            geom = loadswkt( tunn.wkt())
                # Har noen bruer der vegen er lagt ned => intet lokasjonsobjekt 
                # i NVDB api'et. Trenger bedre håndtering av historikk... 
                # Vi får fikse feilhåndtering når det tryner... 
    
            bbox = geom.buffer(1000).bounds
            (ssrtreff, ssrurl) = askSSR( tunndata['Navn'], bbox, debug=debug)         
    
            if ssrtreff == 0:
                    match = 'INGEN'
            elif ssrtreff == 1:
                match = 'EKSAKT'
            elif ssrtreff > 1: 
                match = 'FLERE?'
            
            tunndata['SSRtreff'] = match
            # Reprojiserer, 
            utm33 = pyproj.Proj('+init=EPSG:25833')
            utm32 = pyproj.Proj('+init=EPSG:25832')
            x2,y2 = pyproj.transform(utm33, utm32, geom.x, geom.y) 
    
            tunndata['X_utm32'] = x2
            tunndata['y_utm32'] = y2
            
            tunndata['ssr_url'] = ssrurl
    
            resultat.append(tunndata)
            
        else: 
            print( tunn.id, tunn.egenskapverdi('Navn', empty=''), 'er ikke stedfestet (historisk objekt?)')

        tunn = tunneller.nesteNvdbFagObjekt()

    return resultat
    # nvdb.csv_skriv( 'brunavn.csv', resultat)

if __name__ == '__main__':

    
    resultat = hentNvdbTunnel( debug=False)    
    # sluppen = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272765437') )
    # svin = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272299150') )
    # enkeltNvdbBru( sluppen)
    # enkeltNvdbBru( svin)