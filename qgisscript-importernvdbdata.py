# -*- coding: utf-8 -*-
"""
Script for å interaktivt legge til NVDB-vegnett og fagdata via python 
kommandolinje i QGIS. Se dokumentasjon på bruk av nvdbapi - funskjoner på
https://github.com/LtGlahn/nvdbapi-V2


Legg dette scriptet et sted hvor det er lettvint 
å finne fra QGIS. F.eks. C:\Users\<dittbrukernavn>. 

EKSEMPLER

#Vegnett europaveger Trondheim kommune
v = nvdbVegnett()")
v.addfilter_geo({ 'kommune' : 1601, 'vegreferanse' : 'E' })" ) 
nvdb2qgislag( v, 'Europaveger Trondheim', iface)") 

# Bomstasjoner
b = nvdbFagdata(45)")
nvdb2qgislag(b, 'Bomstasjoner', iface)")

# Søk etter fartsgrenser innenfor kartflaten, legg til 
f = nvdbFagdata(105)
nvdb2kart( f, iface)

"""

import sys
import os 

# Endre stien til dit du har lastet ned biblioteket
# https://github.com/LtGlahn/nvdbapi-V2 
nvdblibrary = 'C:/Data/test/github/nvdbapi-py'
sys.path.append(nvdblibrary)

# Setter miljøvariabel til dit du har biblioteket
os.environ['nvdbapi-dir'] = nvdblibrary

from nvdbapi import *
from nvdb2qgis import * 


