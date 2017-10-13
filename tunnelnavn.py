# -*- coding: utf-8 -*-
"""Henter bruer fra NVDB og sjekker om navnet på brua finnes i Sentralt 
    stedsnavnregister (SSR). Lagrer treffliste til CSV-fil""" 

import nvdbapi
import xmltodict
import requests
import json
from shapely.wkt import loads as loadswkt  
import pdb
import re
import pyproj  
from collections import OrderedDict
import csv

def kortinnnavn( navn, ekstrasnill=False, debug=False): 
    """Fjerner tunnel og anna tjafs fra slutten av NVDB-tunnelnavn"""

    if debug: 
        print( navn)

    
    navn = navn.lower()
    navn = navn.strip()
    

    # Fjerner alle tall
    navn = re.sub( '\d+', '', navn)
    
    forbudsliste1 = [ 'kulvert',
                     'viltovergang',
                        'miljø',
                        'nordgående',
                        'sørgående',
                        'miljø',
                        'vegen', 
                        'overbygg', 
                        'viltlokk',
                        'overbygg',
                        'entunnelen',
                        'ettunnelen',
                        'etunnelen',
                        'itunnelen',
                        'stunnelen',
                        'tunelen',
                        'tunellen',
                        'tunnellen',
                        'tunnelen',
                        'tunnel',
                        ' iii', ' ii',  ' i', ' vest', ' øst' ]
    
    for forb in forbudsliste1: 
        navn = re.sub( forb, '', navn).strip()
        if debug: 
            print( navn, ' => ', forb)
    
    forbudsliste2 = [ 'en', # Til vurdering 
                     'et', 'a', 'an', 's', 'e']    
    
    if ekstrasnill: 
        for forb in forbudsliste2:
            # navn = navn.rstrip(forb).strip()
            navn = re.sub(forb+'$', '', navn).strip()
            if debug: 
                print( navn, ' => ', forb)

    
    return navn 

def askSSR( navn, bbox, debug=False ): 
    """Slår opp i SSR på strengen navn. Wildcard-søk er støttet, ref
    SSR-dokumentasjonen. bbox er en shapely boundingBox-element, dvs en 
    liste med 4 koordinater (nedre venstre øst/nord og øvre høyre øst/nord)
    
    Plukker ut et koordinatpunkt og legger inn som E, N i UTM sone 32
    (epsg:25832)"""
    
    navn2 = navn.strip()
    
    url = 'https://ws.geonorge.no/SKWS3Index/ssr/sok'
    params = {  'maxAnt' : '50', 
        'navn' : navn2 + '*', 
        'ostLL'     : bbox[0],
        'nordLL'    : bbox[1],
        'ostUR'     : bbox[2], 
        'nordUR'    : bbox[3]
        }
    r = requests.get( url, params=params)
    ssrurl = r.url 
    if debug: 
        print( navn, r.url)
            
    if not r.ok: 
        # raise ImportError( "Kan ikke hente data fra SSR: %s" % r.url ) 
        print( "SSR søk feiler", r.text)
        return( 'FEILER', r.url, navn2)
    else: 

        document =  xmltodict.parse( r.text )
        antGodeTreff = 0
        antSSRtreff = int( document['sokRes']['totaltAntallTreff'] )
        SSR_navn = None
        # pdb.set_trace()
                
        if antSSRtreff == 1: 
            if sjekkNavn( document['sokRes']['stedsnavn']): 
                antGodeTreff = 1
                SSR_navn = document['sokRes']['stedsnavn']['skrivemaatenavn']
            
        elif antSSRtreff >= 1: 
            SSRnavneliste = []
            for elem in document['sokRes']['stedsnavn']: 
                if sjekkNavn( elem ):
                    antGodeTreff += 1
                    
                    SSRnavneliste.append( elem['skrivemaatenavn'])
            SSR_navn = ','.join( SSRnavneliste )
            
        
        if antGodeTreff < 0:
            match = 'FEILER'
        elif antGodeTreff == 0:
            match = 'INGEN'
        elif antGodeTreff == 1:
            match = 'EKSAKT'
        elif antGodeTreff > 1: 
            match = 'FLERE'
        
            
        return ( match, ssrurl, SSR_navn)


def sjekkNavn( stedsnavn): 
    """Sjekker om stedsnavn-elementet fra SSR er det vi  vil ha"""

    godstatus = [ u'Vedtatt', u'Godkjent', u'Samlevedtak' ]

    if stedsnavn['navnetype'] == u'Tunnel' and \
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
        tunneller.addfilter_geo( {'kommune' : 105 })
        
    resultat = []
    tunn = tunneller.nesteNvdbFagObjekt()
    while tunn: 

        if tunn.geometri: 
            tunndata = OrderedDict()
            tunndata['Navn'] = tunn.egenskapverdi( 5225)
            tunndata['NVDB_id'] = tunn.id

#            if not tunn.egenskapverdi(5225):
#                print( tunn.id, "Mangler navn")
            
            tunndata['SkiltetLengde'] = tunn.egenskapverdi(8945 )
            
#            if not tunn.egenskapverdi( 8945):
#                print( tunn.id, tunndata['Navn'], "Mangler skiltet lengde")
            
            tunndata['Åpningsår'] = tunn.egenskapverdi( 10383 )
            tunndata['Kommune'] = tunn.lokasjon['kommuner'][0]

            # Finner tunnelløp som datterobjekt av tunnel
            tunnellop = tunn.relasjon( 67)
            
            tunnbarn_antall = 0
            tunnbarn_maksOppgittLengde = 0
            tunnbarn_maksFysiskLengde = 0
            tunnbarn_aapningsaar = 0
            tunnbarn_kommune = set()
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

                        if tunn2.geometri:                      
                            geom2 = loadswkt( tunn2.wkt())
                            tunnbarn_maksFysiskLengde = max( geom2.length, 
                                    tunnbarn_maksFysiskLengde)
                        
                        tunnbarn_kommune.update( tunn2.lokasjon['kommuner'] )
            else: 
                print( tunn.id, tunndata['Navn'], "mangler tunnelløp")
    
            tunndata['AntallTunnelløp'] = tunnbarn_antall
            
            if tunnbarn_maksOppgittLengde == 0: 
                tunnbarn_maksOppgittLengde = None
                
            if tunnbarn_aapningsaar == 0: 
                tunnbarn_aapningsaar = None
            
            tunndata['MaksAngittLengdeTunnelløp'] = tunnbarn_maksOppgittLengde
            tunndata['MaksFysiskLengdeTunnelløp'] = tunnbarn_maksFysiskLengde
            tunndata['ÅpningsårFraTunnelløp'] = tunnbarn_aapningsaar
            tunndata['kommunerTunnelløp'] = ','.join( map( str, tunnbarn_kommune))
       
            geom = loadswkt( tunn.wkt())
                # Har noen bruer der vegen er lagt ned => intet lokasjonsobjekt 
                # i NVDB api'et. Trenger bedre håndtering av historikk... 
                # Vi får fikse feilhåndtering når det tryner... 
    
            bbox = geom.buffer(17000).bounds
            (match, ssrurl, ssrnavn) = askSSR( tunndata['Navn'], 
                                                            bbox, debug=debug)
            soketerm = tunndata['Navn'].strip()
            soketerm2 = None
            if not ssrnavn: 
                # pdb.set_trace()
                soketerm = kortinnnavn( tunndata['Navn'], debug=debug)
                (match, ssrurl, ssrnavn) = askSSR( soketerm, 
                                                            bbox, debug=debug)
                if match == 'EKSAKT': 
                    match = 'EKSAKT-forenklet1'
                if not ssrnavn: 
                    soketerm2 = kortinnnavn( soketerm, ekstrasnill=True, 
                                                               debug=debug)
                    (match, ssrurl, ssrnavn) = askSSR( soketerm2, 
                                                            bbox, debug=debug)
                    if match == 'EKSAKT': 
                        match = 'EKSAKT-forenklet2'

            
            tunndata['SSRtreff'] = match
            tunndata['soketerm'] = soketerm
            tunndata['soketerm2'] = soketerm2
            # Reprojiserer, 
            utm33 = pyproj.Proj('+init=EPSG:25833')
            utm32 = pyproj.Proj('+init=EPSG:25832')
            x2,y2 = pyproj.transform(utm33, utm32, geom.x, geom.y) 
    
            tunndata['X_utm32'] = x2
            tunndata['y_utm32'] = y2
            tunndata['SSR navn'] = ssrnavn
            tunndata['ssr_url'] = ssrurl
    
            resultat.append(tunndata)
            
        else: 
            print( tunn.id, tunn.egenskapverdi('Navn', empty=''), 
                  'er ikke stedfestet (historisk objekt?)')

        tunn = tunneller.nesteNvdbFagObjekt()

    return resultat
    # nvdb.csv_skriv( 'brunavn.csv', resultat)

if __name__ == '__main__':

    
    resultat = hentNvdbTunnel( debug=False)    
    
    with open( 'tunnelnavn_analyse20171013.csv', 'w', encoding='utf-8-sig', 
                                                  newline='',) as outfile: 
        w = csv.DictWriter(outfile, resultat[0].keys(), delimiter=';', 
                                                    quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(resultat)
    
    # sluppen = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272765437') )
    # svin = nvdb.Objekt( nvdb.query( '/vegobjekter/objekt/272299150') )
    # enkeltNvdbBru( sluppen)
    # enkeltNvdbBru( svin)