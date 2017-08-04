# -*- coding: utf-8 -*-
import nvdbapi
import nvdb2geojson
import json
from warnings import warn
# from qgis.core import * 
import qgis

"""
Kommandolinjeverktøy for import av NVDB vegnett og fagdata til QGIS
Bruker nvdb2geojson og mellomlagrer geojson som fil. 
Argumentet er nvdbapi.py er en av klasene nvdbVegnett eller nvdbFagdata
definert i nvdbapi.py

Før bruk må du sette områdefilter og evt egenskapsfilter
"""

def __qgisargs( *args): 
    """Internt metode. Sjekker at vi har QGIS iface - objekt som argument. 
    Kan også ha navn (tekst), som da vil bli brukt som lagnavn i 
    layers panel"""

    navn = None
    
    for aa in args: 
        if isinstance( aa, str): 
            navn = aa
        elif isinstance( aa, qgis._gui.QgisInterface): 
            iface = aa
    
    if not iface or not isinstance(iface, qgis._gui.QgisInterface): 
            raise ValueError("Must have qgis interface iface argument as input" )
            # print("Must have qgis interface iface argument as input" )

    return (navn, iface)    

def __navneforslag( data, objektid='' ): 
    """Gjetter på brukandes navn til QGIS layer-panel"""
    
    navn = 'nvdbdata'
    
    if isinstance( data, dict):
        try: 
            navn = '_'.join( [ str( data['metadata']['type']['id'] ), 
                               data['metadata']['type']['navn'][:7], 
                               str(objektid) ])
        except KeyError: 
            pass
        
    if isinstance( data, list ): 
        navn = '_'.join([ 'veglenke', str(objektid) ] )
    
    if isinstance( data, nvdbapi.nvdbFagdata ): 
        navn = '_'.join( [ str( data.objektTypeId ), 
                               data.objektTypeDef['navn'][:8] ])
                   
    if isinstance( data, nvdbapi.nvdbVegnett ): 
        navn = 'vegnett' 
        
    if isinstance( data, nvdbapi.nvdbFagdata ): 
        navn = '_'.join( [ str( data.objektTypeDef['id']), 
                          data.objektTypeDef['navn'] ])
        
    return navn
   
    
def hentnvdbid( objektid, *args, **kwargs ): 
    """Henter NVDB objekt - fagdata eller veglenke og føyer det til kartflaten 
    i QGIS. Merk at ett strekningsobjekt / en veglenke som regel vil 
    være segmentert i mindre biter. 
    
    MÅ HA argumentet objektid og iface (QGIS interface objekt)
    Kan også ha navn til bruk i layers-meny. (Hvis ikke lages et navn 
    automagisk ut fra objekttype)
    
    EKSEMPEL
    hentnvdbid(808571808, iface )    
    hentnvdbid(808571808, 'vegbredde', iface )    
    
    """ 
    
    data = nvdbapi.finnid(objektid)
    
    (navn, iface) = __qgisargs( *args)

    if data: 
        
        # Navneforslag
        if not navn: 
            navn = __navneforslag( data, objektid=objektid)
        
        
        # Gjetter på at det er NVDB fagdata
        if isinstance( data, dict): 
    
            geojsondata = nvdb2geojson.fagdata2geojson( data, **kwargs)
        
        #Gjetter på at det er vegnett
        elif isinstance(data, list): 
            
            geojsondata = nvdb2geojson.vegnett2geojson( data, **kwargs)
        
        else: 
            warn('Noe galt? Fikk ', type(data), ' for kallet nvdapi.finnid(', 
                  str(objektid), ') forventer dict eller list'  )
            return
        
        if not navn: 
            navn = 'NVDB' 

        tmp = json.dumps( geojsondata )        
        iface.addVectorLayer( tmp, navn, 'ogr')
        
    else: 
        print( 'Fant ingen data for NVDB objektid', str(objektid))

def nvdb2kart(nvdbklasse, *args, **kwargs ): 
    """Tar et søkeobjekt av typen nvdbFagdata eller nvdbVegnett, gjør et søk 
    avgrenset til kartflatens utstrekning i QGIS 
        
    MÅ HA argumentet objektid og iface (QGIS interface objekt)
    Kan også ha navn til bruk i layers-meny. (Hvis ikke lages et navn 
    automagisk ut fra objekttype)
    
    EKSEMPEL
    #Vegnett europaveger 
    v = nvdbVegnett()")
    v.addfilter_geo({ 'vegreferanse' : 'E' })" ) 
    nvdb2kart( v, 'Europaveger Trondheim', iface)") 
    
    # Bomstasjoner
    b = nvdbFagdata(45)")
    nvdb2qgislag(b, 'Bomstasjoner', iface)")
    """    
    
    (lagnavn, iface) = __qgisargs( *args)
    
    # srid = iface.activeLayer().crs().authid() 
    srid = iface.mapCanvas().mapRenderer().destinationCrs().authid()
    if srid == ['EPSG:4326']:
        srid = '4326'
    elif srid in ['EPSG:25833', 'EPSG:32633' ]:
        srid = '32633' 
    else: 
        raise ValueError( 'Kartprojeksjon må være EPSG:4326 eller EPSG:25833' )
        
    xmin = str( iface.mapCanvas().extent().xMinimum())
    xmax = str( iface.mapCanvas().extent().xMaximum())
    ymin = str( iface.mapCanvas().extent().yMinimum())
    ymax = str( iface.mapCanvas().extent().yMaximum())
    
    
    nvdbklasse.addfilter_geo( 
                    { 'kartutsnitt' : ','.join( [ xmin, ymin, xmax, ymax ]), 
                      'srid' : srid } )
    
    nvdb2qgislag( nvdbklasse, lagnavn, iface)
  

def nvdb2qgislag(nvdbklasse, *args, **kwargs): 
    """Tar et søkeobjekt av typen nvdbFagdata eller nvdbVegnett og føyer det 
    til QGIS (uavhengig av gjeldende kartflate). 
    
    Søket bør avgrenses med geografisk filter, eller på annen måte. 
    
    MÅ HA argumentet objektid og iface (QGIS interface objekt)
    Kan også ha navn til bruk i layers-meny. (Hvis ikke lages et navn 
    automagisk ut fra objekttype)
    
    EKSEMPEL
    #Vegnett europaveger Trondheim kommune
    v = nvdbVegnett()")
    v.addfilter_geo({ 'kommune' : 1601, 'vegreferanse' : 'E' })" ) 
    nvdb2qgislag( v, 'Europaveger Trondheim', iface)") 
    
    # Bomstasjoner
    b = nvdbFagdata(45)")
    nvdb2qgislag(b, 'Bomstasjoner', iface)")

    
    """
    
    (lagnavn, iface) = __qgisargs( *args)
    
    if not lagnavn: 
        lagnavn = __navneforslag( nvdbklasse )
        
    # Fagdata - gjetter vi på...? 
    if isinstance( nvdbklasse, nvdbapi.nvdbFagdata) or isinstance(nvdbklasse, dict):
        geojsondata = nvdb2geojson.fagdata2geojson( nvdbklasse, **kwargs)
    elif isinstance( nvdbklasse, nvdbapi.nvdbVegnett) or isinstance( nvdbklasse, list): 
        geojsondata = nvdb2geojson.vegnett2geojson( nvdbklasse, **kwargs)
    else: 
        raise ValueError( "Ikke implementert støtte for denne typen data!") 
    
    tmp = json.dumps( geojsondata )        
    iface.addVectorLayer( tmp, lagnavn, 'ogr')
    
    