# -*- coding: utf-8 -*-
"""
Finner tunnelløp ut fra kjent tunnelID. 
Forutsetter at dette biblioteket er i søkestien (evt i samme mappe): 
https://github.com/LtGlahn/nvdbapi-V2
"""

import nvdbapi 

tunavn = [ 'Frodeåstunnelen']

tunIDer =  [ 237341843, 683535773, 839121631, 
      82277379, 579090124,  842985271]

for tunid in tunIDer: 

    # Henter objekt ut fra ID
    tunnobj = nvdbapi.nvdbFagObjekt( nvdbapi.finnid( tunid))

    # Henter ID til tunnelløpene gjennom relasjon
    tunnlop = tunnobj.relasjon( relasjon=67)
    
    # Holder alle veglenkeposisjoner for tunnelløpene til denne tunellen. 
    veglenker = [ ]
        
    # Henter alle tunnelløp 
    for tlopid in tunnlop['vegobjekter']: 
        tlop = nvdbapi.nvdbFagObjekt( nvdbapi.finnid(tlopid))
        
        # Fisker ut veglenkeposisjoner
        for vlenk in tlop.lokasjon['stedfestinger']: 
            veglenker.append( vlenk['kortform'])
        
    # Henter ulykker 
    ulykker = nvdbapi.nvdbFagdata( 570 )
    
    # Kan evt legge på filter for alvorligste skadegrad
    # Her for Alv.skadegrad=Drept, meget alvorlig skadd eller alv.skadd
    # Ref http://api.vegdata.no/parameter/egenskapsfilter 
    ulykker.addfilter_egenskap( '(5074=6427 OR 5074=6428 OR 5074=6429)')
    
    ulykker.addfilter_geo( { 'veglenke' : ','.join( veglenker) } )
    statistikk = ulykker.statistikk()
    print( statistikk['antall'], 'Ulykker i', 
          tunnobj.egenskapverdi( 'Navn'), tunnobj.id )

    uly = ulykker.nesteNvdbFagObjekt()
    while uly: 
        
        print( '\t', uly.id, uly.egenskapverdi('Ulykkesdato'), 
              'Drepte=', uly.egenskapverdi(5070 ), 
              'MegAlvSkadd=', uly.egenskapverdi(5071), 
              'AlvSkadd=', uly.egenskapverdi(5072), 
              'LettSkadd=', uly.egenskapverdi(5073))
        
        uly = ulykker.nesteNvdbFagObjekt()
    
    