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

def finnveglenkeoverlapp( finndette, blantdisse): 
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

    Keywords: None
        
            
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
            
    tmp = finndette.iloc[ treffidx, :]
    data = tmp.reset_index()
    return data

  
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