# -*- coding: utf-8 -*-
"""
Funksjoner for å finne overlapp mellom to samlinger av NVDB-objekter 
eller en samling NVDB-objekter og samling med veglenkeposisjoner

Bruker pandas / geopandas dataframe til å sortere og filtrere 

Utviklet i python 3, spent på om det blir bakoverkompatibelt med nyere python 2
(burde gå greit såfremt nødvendige bibliotek er installert)

"""


import nvdb2geojson
import geopandas as gpd
from copy import deepcopy
from shapely.geometry import *
from shapely.wkt import loads
import pdb



def fagdata2geodataframe( fagdata, **kwargs ): 
    """Konverterer NVDB fagdata til geodataframe. Se fagdata2geojson 
    fra nvdb2geojson, som denne rutina gjenbruker
    
    Args: 
        fagdata : nvdbFagObjekt fra nvdbapi.py (søkeobjekt som henter data fra
                    NVDB api) ELLER en dict med et enkelt nvdb-objekt fra 
                    vegobjekt/ - endepunktet i NVDB api. 
        
    Keywords: 
        Se fagdata2geojson i nvdb2geojson.py for nøkkeordparametre. 
        
    Returns: 
        Python geopandas (geo)dataframe med nvdb objekter delt opp i 
        individuelle vegsegmenter. 
    
    """
    
    geoj = nvdb2geojson.fagdata2geojson( fagdata, **kwargs)
    mygpd =  gpd.GeoDataFrame.from_features( geoj['features'])
    mygpd.crs = {'init': 'epsg:25833'}
      
    return mygpd

def vegnett2geodataframe( vegnett, **kwargs ): 
    """Konverterer NVDB vegnett til geodataframe. Se vegnett2geojson 
    fra nvdb2geojson, som denne rutina gjenbruker
    
    Args: 
        fagdata : Enten nvdbVegnett-objekt fra nvdbapi.py (søkeobjekt som 
                    henter data fra vegnetts-endepunktet NVDB api) ELLER 
                    en liste med vegnett-lenker på samme datastruktur 
                    som vegnettsdata fra vegnett/ - endepunktet i NVDB api. 
        
    Keywords: 
        Se fagdata2geojson i nvdb2geojson.py for nøkkeordparametre. 
        
    Returns: 
        Python geopandas (geo)dataframe med nvdb objekter delt opp i 
        individuelle vegsegmenter. 
    
    """
    
    geoj = nvdb2geojson.vegnett2geojson( vegnett, **kwargs)
    mygpd =  gpd.GeoDataFrame.from_features( geoj['features'])
    mygpd.crs = {'init': 'epsg:25833'}
      
    return mygpd

def shapely_cut(line, distance):
    """Cuts a line in two at a distance from its starting point
    https://stackoverflow.com/questions/31072945/shapely-cut-a-piece-from-a-linestring-at-two-cutting-points 
    
    """
    
#    if myline.has_z: 
#        line = LineString([xy[0:2] for xy in list(myline.coords)]) 
#    else: 
#        line = myline
    
    if distance <= 0.0 or distance >= line.length:
        return [LineString(line), LineString(line) ]
    
    coords = list(line.coords)
    for i, p in enumerate(coords):
        pd = line.project(Point(p))
        if pd == distance:
            return [
            LineString(coords[:i+1]),
            LineString(coords[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            if line.has_z: 
                return [
                LineString(coords[:i] + [(cp.x, cp.y, cp.z)]),
                LineString([(cp.x, cp.y, cp.z)] + coords[i:])]
            else: 
                return [
                LineString(coords[:i] + [(cp.x, cp.y)]),
                LineString([(cp.x, cp.y)] + coords[i:])]
                        
            

def segmenterveglenkeoverlapp( finndette, blantdisse, debug=False): 
    """Finner overlapp og "klipper til" slik at utstrekningen stemmer
    
    Beregner også nye vegreferanse-verdier og strekningslengde 
    
    
    """
    myoutdata = []
    temp = finndette.to_dict('index')
    for k in temp: 
        fd = temp[k]
        
        blant = blantdisse[( (blantdisse['veglenkeid'] == fd['veglenkeid']) & 
                             (blantdisse['fra_posisjon'] < fd['til_posisjon']) & 
                             (blantdisse['til_posisjon'] > fd['fra_posisjon']) )]

        if debug: 
            print( len(blant), "mulige matcher for", fd['id'], "-", fd['vegsegment nr'], fd['kortform'] )
    
        for idx, row in blant.iterrows(): 
            
            if debug: 
                print( "\t","match", idx, "av", len(blant), "treff for",  fd['id'], "-", fd['vegsegment nr'], fd['kortform'] ) 
                print( "\t","matcher mot:", row['id'], "-", row['vegsegment nr'], row['kortform'] )
            
            
            presisjon = 8            
            if ( round( row['fra_posisjon'], presisjon) == 
                 round( fd['fra_posisjon'], presisjon)) and ( 
                 round( row['til_posisjon'], presisjon) == 
                 round( fd['til_posisjon'], presisjon) ): 
                
                myoutdata.append( fd)
                print( "\teksakt match på veglenkeposisjoner", fd['kortform'])
                
            else: # Må endre utstrekning på veglenkeposisjon, meterverdi og geometri
                
                out = deepcopy( fd)
                
                out['fra_posisjon'] = max( [ row['fra_posisjon'], fd['fra_posisjon']])
                out['til_posisjon'] = min( [ row['til_posisjon'], fd['til_posisjon']])
                
                out['fra_meter'] = max( [ row['fra_meter'], fd['fra_meter']])
                out['til_meter'] = min( [ row['til_meter'], fd['til_meter']])
                out['strekningslengde'] = out['til_meter'] - out['fra_meter']

               
                if (  round( row['fra_posisjon'], presisjon) == 
                      round( out['fra_posisjon'], presisjon) ) and ( 
                      round( row['til_posisjon'], presisjon) == 
                      round( out['til_posisjon'], presisjon) ): 
                    
                    out['geometry'] = row['geometry']
                    
                    if debug: 
                        print( "\t", "gjenbruker blantdette-objektets geometri" )

                elif (round( fd['fra_posisjon'], presisjon) == 
                      round( out['fra_posisjon'], presisjon) ) and ( 
                      round( fd['til_posisjon'], presisjon) == 
                      round( out['til_posisjon'], presisjon) ): 
                    
                    out['geometry'] = fd['geometry']
                    
                    if debug: 
                        print( "\t", "gjenbruker finndette-objektets geometri" )

                        
                else: 
                    
                    # Regner om veglenkeposisjoner til 0-1 intervallet relativt 
                    # på eksisterende geometri
                    plengde = fd['til_posisjon'] - fd['fra_posisjon']
                    posfra = ( out['fra_posisjon'] - fd['fra_posisjon']) / plengde
                    postil = ( out['til_posisjon'] - fd['fra_posisjon'] ) / plengde
                    
                    # Regner om relativ posisjon til avstand i meter
                    fysposfra = posfra * fd['geometry'].length 
                    fyspostil = postil * fd['geometry'].length
                    
                    # Klipper ... 
                    [geom1, geom2] = shapely_cut( fd['geometry'], fyspostil) 
                    [geom3, nygeom] = shapely_cut( geom1, fysposfra)
                    out['geometry'] = nygeom
                    
                    if debug:
                        print( "\tBeregner ny geometri" )
                        print("\t", fd['strekningslengde'] - out['strekningslengde'], "strekningslengde-meter kortere") 
                        print("\t", fd['geometry'].length - out['geometry'].length, "fysiske meter kortere") 
                        print( "\tfd-objekt", fd['fra_posisjon'], fd['til_posisjon'], fd['geometry'].length)
                        print( "\tbd-objekt", row['fra_posisjon'], row['til_posisjon'], row['geometry'].length)
                        print( "\tResultat:", out['fra_posisjon'], out['til_posisjon'])
                        print( "\tberegnet:", posfra, "til", postil, "skalering", plengde) 
                        print( "\tfysisk:", fysposfra, fyspostil)
    
#                    if debug and out['id'] == 261149290: 
#                        pdb.set_trace()
                
                myoutdata.append(out)
                
    if len( myoutdata ) > 0:
        # myfg = pf.DataFrame
        return gpd.GeoDataFrame.from_dict( myoutdata)
    else: 
        return finndette[ finndette['hp'] == -3]
    
def finnveglenkeoverlapp( finndette, blantdisse, returnerindex=False): 
    """Finner overlapp mellom 2 geodataframes med NVDB-objekter eller veglenker

    NB! Skalerer dårlig, bruk kun på små datamengder! 
    
    NB! Skiller ikke mellom hel eller delvis overlapp, og lager ikke ny 
    segmentering. Dvs vi tar ikke hensyn til om finndette-segmentet har større 
    utstrekning enn treffene i blantdisse. 
    
    TODO: 
        - Takle større datamengder (med bedre bruk av indeksering?) 
        - Lag ny segmentering slik at resultatsettet aldri går utover 
            veglenkeposisjonene i blantdisse 

    
    Args: 
        finndette, blantdisse
            (Geo)dataframe med nvdb fagdata eller 
            veglenker, f.eks. laget med funksjonene vegnett2geodataframe 
            eller fagdata2geodataframe. Alternativt vilkårlig (geo)dataframe
            med kolonnene veglenkeid (heltall), fra_posisjon, til_posisjon

    Keywords: 
        returnerindex : Bool (False) Returnerer index til treffene i stedet
            for data
                    
        
            
    Returns: 
        Geodataframe med de elementene i finndisse som overlapper med
        veglenkeID og veglenkeposisjoner i blantdisse
    
    """
    
    treffidx = []
    p1 = blantdisse
    
    for idx, row in finndette.iterrows(): 
        if len( p1[ ( ( p1.veglenkeid == row['veglenkeid']) &
                (p1.fra_posisjon < row['til_posisjon']) & 
                (p1.til_posisjon > row['fra_posisjon'])  )] ) > 0: 
    
            treffidx.append(idx)
    
    if returnerindex: 
        return treffidx
    else: 
        return finndette[ finndette.index.isin(  treffidx) ].copy()

  
"""Eksempler: 
import overlappfunksjoner
import nvdbapi
tent = nvdbapi.nvdbFagdata(826)
tent.addfilter_egenskap( '10946="NO-100.29"')
gpd_tent = overlappfunksjoner.fagdata2geodataframe(tent)

felt = nvdbapi.nvdbFagdata(616)

felt.addfilter_overlapp('826(10946="NO-100.29")')
gpd_felt = overlappfunksjoner.fagdata2geodataframe(felt)
gpd_ektefelt = overlappfunksjoner.finnveglenkeoverlapp(gpd_felt, gpd_tent)
#  gpd_ektefelt.crs = {'init': 'epsg:25833'}
with open( 'feltstrekning.geojson', 'w') as f: 
    f.write( gpd_ektefelt.to_json())
"""