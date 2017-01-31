# -*- coding: utf-8 -*-
"""
Feilsøking på bomstasjoner og innkrevningsretning. 

Henter bomstasjoner fra NVDB, og supplerer med data fra feltstrekning og 
retningsinformasjon fra visveginfo-tjenesten. 

Jeg har en del logikk som sjekker om bomstasjonens innkrevingsretning er 
konsistent med bomstasjonens vegnettstilknytning (felt), og hvordan 
dette samsvarer med mulige felt (hentet fra feltstrekningsobjektet)

Jeg sjekker eksplisitt om metreringsretning avviker fra nettverkets orientering. 
Dette er litt pirkete, og krever flere kall mot ulike endepunkt i 
visveginfo-tjenesten. Spesifikt så: 
    - Jeg får data om vegnettet for veglenkeID og -posisjon fra 
        GetRoadReferenceForNVDBReference. 
        Her finnervvi nettverkets orientering (kompassretning)
        
    - Jeg sjekker metreringsretning ved oppslag på vegreferanse i endepunktet
        GetRoadReferenceForReference. Logikken er å pertubere meterverdi 
        (pluss og minus en meter) og se på veglenkeposisjon. 
        Hvis veglenkeposisjon MINKER når meterverdien ØKER så er metreringsretningen
        motsatt av vegnettets orientering. 
        
   Forutsetning: 
    - Endring på en meter medfører ikke at vi befinner oss på en annen veglenke
        Dette er vel den groveste antagelsen...  
    - Minst ett av vegreferanse-oppslagene (pluss og minus en meter) gir 
        gyldige data


@author: Jan Kristian Jensen
"""

import nvdbapi 
import shapely.wkt

import xmltodict
import requests
from credentials import credentials # Local credentials 
import psycopg2
# from requests.exceptions import ConnectionError
#import pdb


def hentfelt( veglenke, posisjon): 
    
    # Bug, må ha strekning fra-til, ikke match på punkt: 
    delta = 0.0000000001
    if posisjon - delta < 0: 
        a = posisjon
        b = posisjon + 2*delta
    elif posisjon + delta > 1: 
        a = posisjon - 2*delta
        b = posisjon
    else: 
        a = posisjon - delta
        b = posisjon + delta
        
    felt = nvdbapi.nvdbFagdata(616)
    
    geofilter = { 'veglenke' :  str(a) + '-' + str(b) + '@' + str(veglenke) }
    felt.addfilter_geo( geofilter  )
    mittfelt = felt.nesteNvdbFagObjekt()
    if mittfelt: 
        data = mittfelt.egenskapverdi( 'felt', empty='')
    else: 
        data = '1#2'
        print( "Fant ingen feltstrekning for: " + geofilter['veglenke'] )
    # Sjekker om det finnes flere: 
    test = felt.nesteNvdbFagObjekt()
    while test: 
        
        blurp = mittfelt.egenskapverdi('felt')
        if blurp == data: 
            print( 'Fant flere feltstrekningobj ' + geofilter['veglenke'] )
        else: 
            print( 'Fant flere feltstrekningobj DATA MISMATCH' + geofilter['veglenke'])
            
        test = felt.nesteNvdbFagObjekt()
        
    return data
    
def sjekkretning( bom ):

    (innkr, felt, veg) = enkelretning( bom)
    
    if innkr == '0': 
        if felt == 'Begge' or felt == '0': 
            return 'ok'
        else: 
            return 'sjekk'
            
    elif innkr == 'Begge': 
        if felt == 'Begge' or felt == veg or felt == '0': 
            return 'ok'
        else: 
            return 'FEIL'
        
    elif innkr == 'med': 
        if felt == 'med' or veg == 'med': 
            return 'ok'
        else: 
            return 'FEIL'
            
    elif innkr == 'mot': 
        if felt == 'mot' or veg == 'mot': 
            return 'ok'
        else: 
            return 'FEIL'
                
    return 'FEIL'

def effektivretning( bom ): 
    """Returnerer hvilken retning trafikken I PRAKSIS kan gå forbi bomst"""
    
    (innkr, felt, veg) = enkelretning( bom)
    if felt == 'med' and (veg == 'med' or veg == 'Begge'): 
        return 'med'
    elif felt == 'mot' and (veg == 'mot' or veg == 'Begge'): 
        return 'mot' 
    else: 
        return veg
    
    
def felt2retning( felt ): 
    
    if ('1' in felt or '3' in felt) and not '2' in felt and not '4' in felt: 
        return 'med'
    elif ('2' in felt or '4' in felt) and not '1' in felt and not '3' in felt: 
        return 'mot'
    elif felt == '':
        return '0'
        
    else: 
        return 'Begge'
        
    
def enkelretning( bom): 
    """Innkrevingsretning til bomstasjon"""
    
    innkr = ''
    
    if 'Med' in bom['innkrevingsretning']: 
        innkr = 'med'
    elif 'Mot' in bom['innkrevingsretning']: 
        innkr = 'mot' 
    elif 'Begge' in bom['innkrevingsretning']:
        innkr = 'Begge'
    else: 
        innkr = '0' 
        
    felt = felt2retning( bom['felt'])
    veg = felt2retning( bom['muligeFelt'])
    
    return (innkr, felt, veg)

    
def visveginfo_vegreferanseoppslag( vegreftxt ): 
    """Returnerer lenkeposisjon ut fra vegreferanse-oppslag. Returnerer Null 
    hvis oppslaget er ugyldig. 
    """

    
    path = 'GetRoadReferenceForReference'
    params = { 'roadReference' : vegreftxt,  'topologyLevel' : 'Overview' }
    b = anropvisveginfo( path, params )
    
    if 'RoadReference' in b['ArrayOfRoadReference'].keys():
        return float( b['ArrayOfRoadReference']['RoadReference']['Measure'] ) 
    else: 
        return None 
        
def sjekkmetreringretning( vvidata ): 
    """Tar et oppslag mot visveginfo-tjenesten, pertuberer det med positiv og 
    negativ meterverdi og ser om lenkeposisjon øker eller minker. 
    Returnerer kompassretning på metrering
    """
    
    # Initialiserer en del variabler til None
    pos0 = retning = motsatt = None 
    
    hp = vvidata['RoadReference']['TextualRoadReference'][0:14]
    minmeter = int( vvidata['RoadReference']['RoadNumberSegmentDistance'])
    
    minpos = float( vvidata['RoadReference']['Measure'] ) 
    if minmeter >= 1: 
        pos0 = visveginfo_vegreferanseoppslag( hp + str( minmeter-1 ).zfill(5))
        
    pos2 = visveginfo_vegreferanseoppslag( hp + str( minmeter+1).zfill(5))
    
    if pos0 and pos0 > minpos: 
        motsatt = True
        
    if pos2 and pos2 < minpos: 
        motsatt = True
        
    if pos0 and pos2 and pos0 > pos2 and not motsatt: 
        print( '\t'.join( [ 'FEIL METRERINGSLOGIKK', hp, 'm'+str(minmeter) ]  ))
    
    if pos0 or pos2: 
        retning = float( vvidata['RoadReference']['RoadnetHeading']) 
        if motsatt: 
            retning = (retning + 180.0) % 360 

    return retning 
    
def anropvisveginfo( path, params  ): 
    baseurl =  'http://visveginfo-static.opentns.org/RoadInfoService/' 
    
    url = baseurl + path 

    ## Jeg har lagt inn proxy-informasjon i credentials-funksjonen. 
    ## Unødvendig på de fleste hjemmenettverk, påkrevd på en del arbeidsplasser
    #cred = credentials()
    # r = requests.get( url, params=params, proxies=cred['proxies'] )
    r = requests.get( url, params=params )
    
    return xmltodict.parse( r.text )
    
def kompassretning( veglenke, posisjon ):
    
    
    path = 'GetRoadReferenceForNVDBReference'
    params = { 'reflinkoid' : veglenke,  'rellen' : posisjon }
    b = anropvisveginfo( path, params )

    vegnettretn =  b['RoadReference']['RoadnetHeading']
    metreringsretn = sjekkmetreringretning( b ) 
    return (vegnettretn, metreringsretn)
    

def lagre2postgis( data, foupostgis=False ):
    """Lagrer til lokal postgis installasjon"""
    
    cred = credentials()
    # mycred = cred['localpostgis']
    if foupostgis: 
        mycred = cred['foupostgis']
    else: 
        mycred = cred['localpostgis']
    
    conn = psycopg2.connect(database=mycred['database'], 
                            user=mycred['user'] , 
                        password=mycred['pw'], 
                        host=mycred['host'])
    curs = conn.cursor()
    
    curs.execute( 'DROP TABLE IF EXISTS bomstasjoner' )

    curs.execute( 'CREATE TABLE bomstasjoner(geom geometry, id integer PRIMARY KEY NOT NULL, navn text, anlId integer, bomId integer, ekteretning text, felt text, innkrevingsretning text, vegnettretn real, metreringretn real, kompassretn real, muligeFelt text, status text, veg text, veglenke integer, veglenkepos double precision   )' )
    conn.commit() 
    
    for bom in data: 
        #curs.execute( 'INSERT INTO bomstasjoner( geom, id, Navn, anlId, bomId, ekteretning, felt, innkrevingsretning, kompassretn, muligeFelt, status, veg, veglenke, veglenkepos )'
         #                'VALUES( ST_SetSRID(%(geom)s::geometry, %(srid)s), %(id)s, %(Navn)s, %(anlId)s, %(bomId)s, %(ekteretning)s, %(felt), %(innkrevingsretning), %(kompassretn), %(muligeFelt), %(status), %(veg), %(veglenke), %(veglenkepos) )' , 
          #               bom) 
        # conn.commit()
        curs.execute( 'INSERT INTO bomstasjoner( geom, id, navn, anlid, bomid, ekteretning, felt, innkrevingsretning, vegnettretn, metreringretn, kompassretn, muligefelt, status, veg, veglenke, veglenkepos)'
                         'VALUES( ST_SetSRID(%(geom)s::geometry, %(srid)s), %(id)s, %(Navn)s, %(anlId)s, %(bomId)s, %(ekteretning)s, %(felt)s, %(innkrevingsretning)s, %(vegnettretn)s, %(metreringretn)s, %(kompassretn)s, %(muligeFelt)s, %(status)s, %(veg)s, %(veglenke)s, %(veglenkepos)s )' , 
                         bom) 
        conn.commit()
        
        
### Start her! 

data = []
bomstasjoner = nvdbapi.nvdbFagdata(45)
# Henter bomstasjoner med gyldige verdier for bomst.id og bompengeanlegg.id
# bomstasjoner.addfilter_egenskap( '9596!=null AND 9595!=null' )

# bomstasjoner.addfilter_egenskap( '9595=15 AND 9596=8')

print( [ 'Filtre: ', bomstasjoner.allfilters()] )
bomst = bomstasjoner.nesteNvdbFagObjekt()


while bomst: 

    print( bomst.egenskapverdi('Navn bomstasjon'))

    tmp = { 'felt' : ''}
    
    tmp['id'] = bomst.id 
    tmp['Navn'] = bomst.egenskapverdi('Navn bomstasjon')
    tmp['bomId'] = bomst.egenskapverdi(9595)
    tmp['anlId'] = bomst.egenskapverdi(9596)
    tmp['innkrevingsretning'] = bomst.egenskapverdi( 9414, empty='')
    tmp['veg'] = bomst.lokasjon['vegreferanser'][0]['kortform']
    tmp['veglenke'] = bomst.lokasjon['stedfestinger'][0]['veglenkeid']
    tmp['veglenkepos'] = bomst.lokasjon['stedfestinger'][0]['posisjon']
    if 'felt' in bomst.lokasjon['stedfestinger'][0]: 
        tmp['felt'] = bomst.lokasjon['stedfestinger'][0]['felt']
    tmp['geom'] = shapely.wkt.loads( bomst.lokasjon['geometri']['wkt']).wkb_hex
    
    tmp['muligeFelt'] = hentfelt( tmp['veglenke'], tmp['veglenkepos'])
    tmp['ekteretning'] = effektivretning( tmp )
    tmp['srid'] = 25833
    
    tmp['status'] = sjekkretning( tmp )
    (tmp['vegnettretn'], tmp['metreringretn']) = kompassretning( tmp['veglenke'], tmp['veglenkepos'])
    
    if tmp['ekteretning'] == 'mot': 
        tmp['kompassretn'] = (float(tmp['vegnettretn']) + 180.0) % 360 
    else: 
        tmp['kompassretn'] = tmp['vegnettretn']
    
    
#    
    data.append( tmp )
    # tbomst = bomst
    bomst = False
    # bomst = bomstasjoner.nesteNvdbFagObjekt() 
    
    
# lagre2postgis( data)