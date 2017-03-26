# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 19:11:33 2017

@author: jan
"""
import pandas as pd
import nvdbapi


excelfilename = 'D:/Brukere/jan/Nedlastinger/Bomstasjoner med timesregel alle regioner 270217.xlsx'
ex = pd.ExcelFile( excelfilename )
df = ex.parse( ex.sheet_names[0])

cnavn = 'Passerings-gruppe for timesregel'

dfclean = df[ df[cnavn].notnull()]
             
takstgrupper = dfclean[cnavn].unique().astype(int)

endringer = []

for t in takstgrupper: 
    dtemp = dfclean[ dfclean[cnavn].astype(int) == t]
    endr1 = {}
    takstgr = dtemp.iloc[0,4] * 10000 + t
    # Spesialbehandling Oslo og Bærum
    # bruker kommunenummer
    if takstgr == 230023: 
        takstgr = 230301
    elif takstgr == 230024:
        takstgr = 230219
    endringer.append( { 'passeringsgruppe' : takstgr, 'df' : dtemp  }  )
    print(takstgr )    
        

# Henter data fra NVDB

#for endr in endringer: 

# Tar et greit eks å starte med. 
# Må iterere over alle mulige passeringsgruppe-verdier
endr = endringer[23] # Bomgringen i Oslo - Asker/bærum
endr['nvdbobjekter'] = []
endr['nvdbendringer'] = []
b = nvdbapi.nvdbFagdata(45)


# Må iterere over alle bomstasjoner innennfor denne gruppen. 
# Plukker for enkelhets skyld ut den første forekomsten... 
for ii, junk in enumerate( endr['df']): 
# ii = 0

    b.refresh()
    # Slå fast hvilke verdier vi skal ha for 9412 timesregel og 10952 varighet
    tim9412 = 13257 # Standard. 
    if endr['df'].iloc[ii,8] ==  'Omvendt timesregel': 
        tim9412 = 18299
    
    tim10952 = endr['df'].iloc[ii,7]
    # Bomstasjon har to NVDB-objekter med samme ID 
    b.addfilter_egenskap('9595='+str(endr['df'].iloc[ii,3])+' AND ' + 
                         '9596='+str(endr['df'].iloc[ii,4]))
    
    b1 = b.nesteNvdbFagObjekt()
    while b1: 
        endr['nvdbobjekter'].append( b1)
        
        # Mal for NVDB endringer 
        nvdbendring = {  
                "typeId" : "45",
                "versjon" : str( b1.metadata['versjon'] ) , 
                "nvdbId" :  str( b1.id ), 
                "egenskaper" : []
                }
        
        # Sjekker om egenskapene må oppdateres i NVDB
        # Timesregel? 
        if tim9412 != b1.enumverdi( 9412 ): 
            nvdbendring['egenskaper'].append( { "typeId" : "9412", 
                                                "operasjon" : "oppdater", 
                                                "verdi" : [ str(tim9412)]}   )
        
        # Varighet
        if tim10952 != b1.enumverdi( 10952): 
            nvdbendring['egenskaper'].append( { "typeId" : "10952", 
                                                "operasjon" : "oppdater", 
                                                "verdi" : [ str(tim10952)]}   )
        # Passeringsgruppe        
        if endr['passeringsgruppe'] != b1.enumverdi( 10951): 
            nvdbendring['egenskaper'].append( { "typeId" : "10951", 
                                                "operasjon" : "oppdater", 
                                                "verdi" : [ str(endr['passeringsgruppe'])]}   )
             
        if len( nvdbendring['egenskaper'] ) > 0: 
            endr['nvdbendringer'].append( nvdbendring)
        
        b1 = b.nesteNvdbFagObjekt()
    

endringmal = {    "datakatalogversjon": "2.08",
                    "effektDato": "2017-03-11",
                    "delvisOppdater": {
                        "vegObjekter": [{
                            "typeId": "45",
                            "versjon": "4",
                            "nvdbId": "82304293",
                            "egenskaper": [{
                                "typeId": "5225",
                                "operasjon": "oppdater",
                                "verdi":  [ "Fjasetorghattunnelen" ]
                            }]
                        }]
                    }
                }
                            


# Skal endre egenskapene: 
# 10951 - Timesregel, passeringsgruppe. HELTALL
# 10952 - Timesregel, varighet. HELTALL (antall minutt)
# 9412 - Timesregel. ENUM 
#          "id": 13257, "Standard timesregel",
#          "id": 13258, "Ikke timesregel",
#          "id": 18299, "Omvendt timesregel",


