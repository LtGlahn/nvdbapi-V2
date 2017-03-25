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

endr = endringer[23] # Bomgringen i Oslo - Asker/bærum
b = nvdbapi.nvdbFagdata(45)
ii = 0
b.addfilter_egenskap('9595='+str(endr['df'].iloc[ii,3])+' AND ' + 
                     '9596='+str(endr['df'].iloc[ii,4]))


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


