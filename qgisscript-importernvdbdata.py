# -*- coding: utf-8 -*-
"""
Script for å interaktivt legge til NVDB-vegnett og fagdata via python 
kommandolinje i QGIS. Se dokumentasjon på bruk av nvdbapi - funskjoner på
https://github.com/LtGlahn/nvdbapi-V2


Legg dette scriptet et sted hvor det er lettvint 
å finne fra QGIS. F.eks. C:\Users\<dittbrukernavn>. 
"""

import sys

# Endre stien til dit du har lastet ned biblioteket
# https://github.com/LtGlahn/nvdbapi-V2 
sys.path.append('C:/Data/test/github/nvdbapi-py')

from nvdbapi import *
from nvdb2qgis import * 


print( "KLAR! Eksempler: \n") 
print( "v = nvdbVegnett()")
print( "v.addfilter_geo({ 'kommune' : 1601, 'vegreferanse' : 'E' })" ) 
print( "nvdb2qgislag( v, 'Europaveger Trondheim', iface)") 
print( "\n")

print( "b = nvdbFagdata(45)")
print("nvdb2qgislag(b, 'Bomstasjoner', iface)")
print("\n")
