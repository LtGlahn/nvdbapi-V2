# -*- coding: utf-8 -*-
"""
PERSONAL - PERSONLIG - UNSTABLE - active development

diverse småsnutter jeg kladder og knotter på, og der det er kjekt for meg 
å bruke git for lettvint synkronisering mellom mine ulike maskiner. 

Finner du noe nyttig her, så vær så god! Men ikke forvent at noe som helst 
funker, eller at du finner det igjen i morra! Det som er levedyktig vil 
gjerne bli plassert andre steder, under andre navn. 

"""

import nvdbapi 
import shapely.geometry
import shapely.wkt
import numpy as np
import pdb
# from proj_wrapper import Proj, coord, PJ


def regnutnyhoyde( mytuple, dato):
    """Regner om fra ellipsoide til ortometrisk NN54 hoyde
    
    Args: 
        mytuple (tuple med x,y,z) - Koordinatene UTM33 euref89 m ellipsoide-z
        dato (tekst) - dato for innmåling på formatet '2018-07-19'
    
    Returns: 
        Koordinat- tuple med ny z-verdi 
        
    """
    
    diff = 9999
    
    s = dato.split('-')
    datotall = float( s[0]) + float( s[1])/12

#    c1 = coord( mytuple[0], mytuple[1], mytuple[2], datotall)
#    r1 = p.trans(c1)
#    diff = r1.xyz.z - c1.xyz.z 
    return( (mytuple[0], mytuple[1], mytuple[2]-diff ) )


def finnellipsoidehoyder( objtype, egengeomtype=['Geometri, Punkt', 
                                                  'Geometri, Linje' ], 
                                    egenskapfilter=None, geofilter=None, 
                                    miljo='prod'): 
    """Første steg i korreksjon ellipsoide=>ortometriske høyder
    
    Leter etter objekter der egengeometri er registrert med 
    ellipsoidehøyder,  slik at disse kan korrigeres med Kartverkets 
    høydetransformasjon. 
    
    Bruker spørrefunksjonene i NVDB api via nvdbapi.py 
    https://github.com/LtGlahn/nvdbapi-V2/ 
    
    Args: 
        objtype (int): Objekttype.id etter NVDB datakatalog
                
    Keywords
        egengeomtype (list of int or text): Liste med hvilke(n) egenskapstype 
                                med egengeometrier som skal korrigeres. 
        egenskapfilter (dict) : Egenskapsfilter, se nvdbapi.nvdbFagdata
        geofilter (dict)      : Områdefilter (geofilter), se nvdbapi.nvdbFagdata
        miljo (text)          : Angir om vi skal hente data fra NVDB produksjon 
                               (default) eller et annet miljø (utv, test)
        
    Returns
        Liste med de NVDB-data som skal endres
    
    
    """ 
    
    data = nvdbapi.nvdbFagdata(objtype)
    if egenskapfilter:
        data.addfilter_egenskap(egenskapfilter)
        
    if geofilter:
        data.addfilter_geo( geofilter)
    
    if miljo != 'prod': 
        data.miljo( miljo)
    
    resultat = []    
    
    mittobj = data.nesteForekomst()
    
    endringsett_vegobjekter = []

    count = 0    
    while mittobj: 
        count += 1
        
        if sjekkellipsoidehoyde(mittobj, egengeomtype): 

            endringsett_element = fiksellipsoidehoyde( mittobj)
            if endringsett_element: 
                endringsett_vegobjekter.append( endringsett_element )
            
            resultat.append(mittobj)
            
            # Itererer over datterobjekter
            if 'barn' in mittobj['relasjoner'].keys(): 
                for barn in mittobj['relasjoner']['barn']: 
                    for vegobj in barn['vegobjekter']:  
                        parametre = { 'inkluder' : 'alle' }
                        r = data.anrope( 'vegobjekter/' + 
                                str(barn['type']['id']) + '/' + str(vegobj), 
                                parametre=parametre) 
                        if r and sjekkellipsoidehoyde(r, egengeomtype): 
                            resultat.append( r)
            
        mittobj = data.nesteForekomst()
    
    print( f'sjekket {count} obj av type {objtype}, korrigerer {len(resultat)}')
    return resultat

def fiksliste_ellipsoidehoyde( mylist, egengeomtype=['Geometri, Punkt', 
                                                  'Geometri, Linje' ]): 
    """Tar en ferdig liste med NVDB-objekter som skal korrigeres og returnerer
    vegobjekter-delen av endringssett
    
    Gjøres slik pga manglende tilgang til UTV-miljøet fra der jeg tester koden"""
    
    endringsett_vegobjekter = []
    for mittobj in mylist: 
        if sjekkellipsoidehoyde(mittobj, egengeomtype): 

            endringsett_element = fiksellipsoidehoyde( mittobj)
            if endringsett_element: 
                endringsett_vegobjekter.append( endringsett_element )

        
    return endringsett_vegobjekter

def fiksellipsoidehoyde( vegobjekt, egengeomtype=['Geometri, Punkt', 
                                                  'Geometri, Linje' ]): 
    
    """Fikser ellipsoidehøyder => ortometrisk høyde vegobjekts egengeometri 
    
    Args
        vegobjekt (dict) Et NVDB vegobjekt hentet fra NVDB api V2 med 
                         https://github.com/LtGlahn/nvdbapi-V2/ 
    
    Keywords: 
        egengeomtype (list) Angir hvilke egenskapsverdier med egengeometri
                            som skal korrigeres
                            
    Returns:
        Et endringssett-vegobjekt som kan sendes inn til NVDB skriveapi 
        (for delvisOppdatering eller delvisKorreksjon)
    
    """ 

    if not sjekkellipsoidehoyde(vegobjekt, egengeomtype): 
        return None
        
    endring_egenskaper = [ ]
    nvdbFagObj = nvdbapi.nvdbFagObjekt( vegobjekt)
    for egtype in egengeomtype: 
        egverdi = nvdbFagObj.egenskapverdi(egtype )
        if egverdi:  
            myshape = shapely.wkt.loads( egverdi)
            nygeomarr = []
            nyshape = None
            if myshape.type in ['Point', 'LineString'] and myshape.has_z: 
               gmlgeomarr = myshape.coords[:]
               
               for mypoint in gmlgeomarr: 
                   nygeomarr.append( regnutnyhoyde( mypoint, 
                                        nvdbFagObj.metadata['startdato']))
                
               if myshape.type == 'Point': 
                    nyshape = shapely.geometry.Point( nygeomarr)
               elif myshape.type == 'LineString': 
                    nyshape = shapely.geometry.LineString( nygeomarr)
                
            elif myshape.type == 'MultiLineString' and myshape.has_z: 
                multiarr = []
                for linestring in myshape.geoms[:]:
                    singlearr = []
                    gmlgeomarr = linestring.coords[:]
                    for mypoint in gmlgeomarr: 
                        singlearr.append( regnutnyhoyde( mypoint, 
                                        nvdbFagObj.metadata['startdato']))
            
                    multiarr.append( singlearr)
                # Forenkle multilinestring m 1 element => linestring? 
                if len( multiarr ) == 1: 
                    nyshape = shapely.geometry.LineString( multiarr[0])
                else: 
                    nyshape = shapely.geometry.MultiLineString( multiarr)
            
            else: 
                print( myshape.type, 'geometritype ikke implementert')
            
            if nyshape: 
                nyegenskap = formulergeometri( nvdbFagObj.egenskap(egtype), nyshape.wkt )
                if nyegenskap: 
                    endring_egenskaper.append( nyegenskap)

    if endring_egenskaper: # Noe verdt å skrive? Lag endringsett-nvdbobjekt
        endring = {     'nvdbId'     : nvdbFagObj.id, 
                        'versjon'    : nvdbFagObj.metadata['versjon'], 
                        'typeId'     : nvdbFagObj.metadata['type']['id'], 
                        'egenskaper' : endring_egenskaper, 
                        'operasjon'  : 'oppdater'
                     }
        
        return endring

    
def formulergeometri( gammelgeom, nywkt ): 
    """Formulerer ny egengeometri-egenskap slik den skal skrives"""
    
    # "verdi": [
    #           "datafangstdato=2016-09-09;målemetode=96;målemetodeHøyde=96;nøyaktighet=1;nøyaktighetHøyde=1;synbarhet=0;maksimaltAvvik=1;temakode=9001;medium=1;sosinavn=FLATE;kommune=1601;verifiseringsdato=2016-09-10;oppdateringsdato=2016-09-11;høydereferanse=2;referansegeometri=1;srid=32633;POLYGON Z ((278220 7034016 123.45, 279220 7035016 246.78, 270220 7036016 226.78, 278220 7034016 123.45))"
    #         ]
    
    kvaltekst = ''
    if "kvalitet" in gammelgeom.keys(): 
        for kval in gammelgeom['kvalitet'].keys(): 
            kvaltekst = ''.join( [ kvaltekst, kval, '=', 
                                  str( gammelgeom['kvalitet'][kval]), ';' ] )
            
    verditekst =  kvaltekst + nywkt
    return { "typeId" : gammelgeom['id'], "verdi" : [ verditekst ]} 




    
def sjekkellipsoidehoyde(mittobj, egengeomtype): 
    """Sammenligner egengeometri med vegnett og finner GROVE feil i høyde
    
    Args: 
        mittobj (dict) Et nvdb objektet fra NVDB api V2, levert av nvdapi.py
        egengeomtype (list of int, text) ID eller navn på egengeometri-egenskap
            Kan være mer enn én. 
    
    Returns: 
        True | False 
        
    # Når har et objekt feil høyde? 
    1) Egengeometri.høyde > vegnettsgeometri.høyde + ca 20-30'ish meter
    2) Ikke under havets overflate (ligger en del høyde=0m verdier i NVDB)

    Punkt 1) kan være litt tricky, fordi differansen ortometrisk-ellipsoidisk
    høyde varierer fra 18 til 48 meter. 
    
    Metode: 1) Vegnettshøyde > -10m. 2) Høydeforskjell egengeometri-vegnett 
    skal være > 17m. 

    """
    hoydediff = 17
    feilhoyde = False
    
    m = nvdbapi.nvdbFagObjekt( mittobj)
    
    for i, vegsegment in enumerate( m.vegsegmenter): 
        if i == 0: 
            vegnettgeom = wkt2numpyarr( vegsegment['geometri']['wkt']) 
        else: 
            np.concatenate( vegnettgeom, 
                           wkt2numpyarr( vegsegment['geometri']['wkt']))

    
    for geomtyp in egengeomtype: 
        egen_wkt = m.egenskapverdi(geomtyp)
        if egen_wkt: 
            egengeom = wkt2numpyarr( egen_wkt )
            
            dz_median = np.median( egengeom[:,2] ) - np.median( vegnettgeom[:,2])
            if dz_median > hoydediff : 
                feilhoyde = True
            
            print( "Høydedifferanse", dz_median )

    return feilhoyde
    

def wkt2numpyarr( wktstring): 
    """Bruker shapely-bibioteket til å omsette WKT => numpy nx3 array med x,y,z 

    Point, Linestring er trivielt, 1x3 eller nx3 numpy-arr
    For MultiLineString så slås alle LineString-elementene sammen
    
    Det samme er planen med Polygon og MultiPolygon (ikke implementert)
    
    Args: 
        wktstring - koordinater med Well Known Tekst 
    
        
    Returns
        numpy nx3 ndarray med x,y,z 
    
    """

    mygeom = shapely.wkt.loads( wktstring)
    
    if mygeom.type == 'Point' or mygeom.type == 'LineString': 
        return np.array( mygeom.coords[:]) 
        
    elif mygeom.type == 'MultiLineString': 
        tmparr = []
        for ii, linestring in enumerate( mygeom.geoms): 
            if ii == 0: 
                tmparr = linestring.coords[:]
            else: 
                tmparr.extend( linestring.coords[:])
                
        return np.array( tmparr ) 

    elif mygeom.type == 'Polygon':
        raise NotImplementedError

    elif mygeom.type == 'MultiPolygon':
        raise NotImplementedError

    else: 
        print( "Kan ikke dekode WKT strengen", wktstring[0:15])
        
    