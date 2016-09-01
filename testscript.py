from nvdbapi import *

if __name__ == "__main__":

    v = nvdbVegnett()
    v.addfilter_geo( { 'kommune' : 1601 } )
    v.addfilter_geo( { 'vegreferanse' : 'ev6hp15' } )
    minveg = v.nesteForekomst()
    while minveg: 
        print( minveg['vegreferanse']['kortform'],  )
        minveg = v.nesteForekomst()
    
        
    
    p = nvdbFagdata( 809) # Døgnhvileplass 
    p.addfilter_egenskap( '9246=12886 AND 9273=12940') 
    p.paginering['antall'] = 3
    o = p.nesteForekomst()
    while o: 
        print( '{} {}'.format( o['id'], o['lokasjon']['vegreferanser'][0]['kortform'] ) )
        for eg in o['egenskaper']: 
            if eg['navn'] == 'Navn': 
                print( eg['navn'], eg['verdi'] ) 
            
        o = p.nesteForekomst()
        
    
    
    myownlist = []	
    p.refresh()
    t = p.nestePaginering() 
    while t: 
        myownlist.extend( p.data['objekter']) 
        t = p.nestePaginering()
        
    # MyownList holder nå kopi av alle data ihht søkekriterier
    print( len( myownlist ))
    print( p.antall)
    p.statistikk()

    p.egenskaper()
    p.egenskaper(9245)
    p.egenskaper('Vask')