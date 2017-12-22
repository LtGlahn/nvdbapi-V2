# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 21:34:03 2017

@author: Jan Kristian Jensen
"""
import shapely
from shapely.ops import linemerge
from shapely.wkt import loads, dumps

import json
import requests 
import copy 
import pdb

def spleisveglenkesegmenter( lenkebiter, slettgeometri=False): 
    """Spleiser korte deler av veglenke til lengre sammenhengende biter
    
    Tar en liste med veglenke-deler (segmenter) og skjøter dem sammen til ett 
    eller flere sammenhengende biter. 
    
    NB! Listen må være sortert, og kun ha data for en veglenke! 
    
    Skal kunne håndtere følgende case: 
        1) Pent strukturerte segmenter i rekkefølge, det ene overtar 
            der det andre slutter. Eksempel: 
            https://www.vegvesen.no/nvdb/api/v2/vegnett/lenker/2631223.json
            
        2) Segmentene overlapper hverandre. (F.eks data til 911-registrering)
    
        3) Segmenter er kun delvis sammenhengende (veglenka er delvis historisk)
        https://www.vegvesen.no/nvdb/api/v2/vegnett/lenker/72852.json
        som er 3 sammenhengende deler fordelt på 48 segmenter
    
    """
    
    nylenke = {}
    andrelenker = [] # Liste for der du har brudd i serien 
    for lenk in lenkebiter: 
        
        if not nylenke: 
            nylenke = copy.deepcopy( lenk)  
            nylenke.pop( 'geometri', 0)
#            nylenke['segmenter'] = [ lenk ]
            if not slettgeometri: 
                nylenke['geometri'] = { 'wkt' : '' }
                nylenke['geometribiter'] = []
                nylenke['geometribiter'].append( loads( 
                                                    lenk['geometri']['wkt']))
                
            # Estimerer total strekningslengde for HELE lenken
            nylenke['totalLengde'] = float( nylenke['strekningslengde'])  / ( 
                float( nylenke['sluttposisjon'] )  - 
                    float( nylenke['startposisjon'] )  )
        
        else: 
            
            # Forutsetter at lenkene er sortert: 
            if  lenk['veglenkeid']  == nylenke['veglenkeid'] and \
                lenk['startposisjon'] <= nylenke['sluttposisjon'] and \
                lenk['sluttposisjon'] >= nylenke['startposisjon']:
                
                    nylenke['startposisjon'] = min( lenk['startposisjon'], 
                                                   nylenke['startposisjon'])

                    nylenke['sluttposisjon'] = max( lenk['sluttposisjon'], 
                                                   nylenke['sluttposisjon'])
                    
                    if not slettgeometri: 
                        nylenke['geometribiter'].append( loads( 
                                                lenk['geometri']['wkt']))
#        
#                    nylenke['segmenter'].append( lenk)
                    
                    nylenke['strekningslengde'] += lenk['strekningslengde']
            else: 
                andrelenker.append( lenk)
             
    # Slår sammen geometri 
    if not slettgeometri: 
        tempgeom = shapely.ops.linemerge( nylenke['geometribiter'])
        nylenke['geometri']['wkt'] = dumps(tempgeom)
    
 
    # Runder av startposisjon _*ørlite grann*_ oppover
    if float( nylenke['startposisjon'] ) > 0: 
        delta = 0.00000001
        nypos  = float( nylenke['startposisjon']) + delta 
        nylenke['startposisjon' ] = str( nypos)
    
    # Runder av sluttposisjon _*ørlite grann*_ nedover
    if float( nylenke['sluttposisjon'] ) < 1: 
        delta = 0.00000001
        nypos  = float( nylenke['sluttposisjon']) - delta 
        nylenke['sluttposisjon' ] = str( nypos)
    
    
    nylenke['kortform'] = str(nylenke['startposisjon']) + '-' + \
        str(nylenke['sluttposisjon'] ) + '@' + str(nylenke['veglenkeid'])
        
    # Beregner ny strekningslengde 
    nylenke['strekningslengde'] = nylenke['totalLengde'] * ( 
        float( nylenke['sluttposisjon']) - float( nylenke['startposisjon']) )
    

    # Fjerner de egenskapene vi (inntil videre) ikke bearbeider: 
    sletteliste = [ 'metadata', 'felt', 'medium', 'temakode', 
                   'konnekteringslenke', 'startnode', 'sluttnode', 
                   'region', 'fylke', 'vegavdeling', 'kommune', 
                   'vegreferanse' ]
    for slett in sletteliste: 
        nylenke.pop( slett, 0)
    
    
    
    
    # Håndterer resten av lenkene: 
    resten = []
    if andrelenker: 
        resten = spleisveglenkesegmenter( andrelenker, slettgeometri=slettgeometri )
    

    nylenke.pop( 'geometribiter', 0)    
    returdata = [ nylenke ]
    returdata.extend( resten )
    return returdata

if __name__ == "__main__":
    
    r = requests.get('https://www.vegvesen.no/nvdb/api/v2/vegnett/lenker/2631223.json' )
    seg1 = r.json()
    lenke1 = spleisveglenkesegmenter( seg1, slettgeometri=True)
    
    r = requests.get('https://www.vegvesen.no/nvdb/api/v2/vegnett/lenker/72852.json' )
    seg2 = r.json()
    lenke2 = spleisveglenkesegmenter( seg2, slettgeometri=True)
    