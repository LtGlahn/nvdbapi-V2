"""
Klasser og funksjoner for å føye NVDB vegnett og fagdata til QGIS 3


"""
from qgis.core import QgsProject,  QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, QgsLineString
from nvdbapi import nvdbVegnett, nvdbFagdata, nvdbFagObjekt, finnid


def mytest():
    
    mem_layer = QgsVectorLayer( "Point?crs=epsg:25833&field=id:integer" + \
        "&field=description:string" + \
        "&index=yes", 
        "Test", 
        "memory") 
        
    QgsProject.instance().addMapLayer(mem_layer) 
    
    mem_layer.startEditing()
    mypoint = QgsPoint( 274549,7042095)
    myfeat = QgsFeature()
    myfeat.setGeometry( QgsGeometry.fromPointXY( mypoint) ) 
    myfeat.setAttributes([ 1, 'Test']) 
    mem_layer.addFeature(myfeat) 
    mem_layer.commitChanges()
    
    print( "Fanken æ e flink!") 
    

def lagGeomFraWkt(): 

    mem_layer = QgsVectorLayer( "Point?crs=epsg:25833&field=id:integer" + \
        "&field=description:string" + \
        "&index=yes", 
        "Test", 
        "memory") 
        
    QgsProject.instance().addMapLayer(mem_layer) 
    
    mem_layer.startEditing()
    myfeat = QgsFeature()
    myfeat.setGeometry( QgsGeometry.fromWkt( 'POINT ( 274539 7042095)' ) ) 
    myfeat.setAttributes( [2, 'fra WKT']) 
    mem_layer.addFeature(myfeat) 
    mem_layer.commitChanges()
    
    print( "Fanken æ e flink!") 

# linjelag = QgsVectorLayer( "Linestring?crs=epsg:25833&field=id:integer&field=description:string&index=yes", "Testlinje", "memory") 

class memlayerwrap(): 
    """
    Wrapper rundt QGIS memorylayer. Blir først synlig i QGIS når du føyer til features. 
    
    Tanken er å ha en smidig håndtering av all den mangfoldighet av geometrityper du finner i NVDB. 
    Et NVDB-objekt kan være POINT, LINESTRING, MULTILINESTRING eller POLYGON (og kanskje litt mer). 
    Og du vet ikke hva du får før du leser inn data.
    
    Inntil videre oversetter vi alle koordinater til 2D.  
    
    Derfor oppretter vi en bunch med tomme lag, en per aktuell geometritype. Og disse føyes først til 
    QGIS når det kommer et NVDB-objekt med aktuell geometritype
    """
    def __init__(self, geomtype, egenskapdef, navn) : 
        self.active = False
        self.geomtype = geomtype
        self.layer = QgsVectorLayer(geomtype + '?crs=epsg:25833&index=yes&' + egenskapdef, navn, 'memory')
        
    def addFeature(self, mittobj):
        if not self.active:
            QgsProject.instance().addMapLayer(self.layer)
            self.layer.startEditing() 
            self.active = True 
        
        feat = QgsFeature()    
        feat.setAttributes( mittobj['egenskaper'] )
        mygeom = QgsGeometry.fromWkt( mittobj['wktgeom'] )
        
        # Tricks for å tvinge 3d => 2d koordinater
        if 'Point' in self.geomtype: 
            feat.setGeometry( QgsGeometry.fromPointXY( mygeom.asPoint()) )  
        elif 'Linestring' in self.geomtype: 
            pass 
        
            # feat.setGeometry(  )
        self.layer.addFeature(feat)
        
    def ferdig( self): 
        if self.active: 
            self.layer.commitChanges()

#class egenskapmapping( ): 
#    """
#    Lager mapping mellom NVDB datakatalog-definisjon => qgis lagdefinisjon. 
#    """
#    
#    def __init__(self, fagdataobj): 
#    
#        self.objektTypeId = fagdataobj.objektTypeId
        
        
def qgisdakat(  fagdataobj):
    """Lager attributt-definisjon for QGIS objekter ihht datakatalogen"""
    # Liste med ID'er for egenskapstypene for denne objekttypen  
    egIds = [] 
    # Liste med QGIS datatyper. Matcher listen med egenskapstyper. 
    qgisEg = []
    dakat = fagdataobj.anrope( 'vegobjekttyper/' + str( fagdataobj.objektTypeId) )

    for eg in dakat['egenskapstyper']: 
        egIds.append( eg['id'] ) 
        qgisEg.append( egenskaptype2qgis( eg) ) 
    
    
    return egIds, qgisEg
        
def egenskaptype2qgis( egenskaptype): 
    """
    Omsetter en enkelt NVDB datakatalog egenskapdefinisjon til QGIS lagdefinisjon-streng
    """
    defstring = egenskaptype['navn']
    if 'Tall' in egenskaptype['datatype_tekst']:
        if 'desimaler' in egenskaptype.keys() and egenskaptype['desimaler'] > 0:  
            defstring += ':double'
        else: 
            defstring += ':int' 
    elif 'Dato' == egenskaptype['datatype_tekst']:
        defstring += ':date'  
    else: 
        defstring += ':string' 
    
    return defstring 
    
#Tekst - Eksempel: Strindheimtunnelen
#Tall - Eksempel: 86
#Flyttall - Eksempel: 86.0
#Kortdato - Eksempel: Måned-dag, 01-01
#Dato - Eksempel: År-Måned-dag, 2015-01-01
#Klokkeslett - Eksempel: 13:37
#Geometri - Geometrirepresentasjon
#Struktur - Verdi sammensatt av flere verdier
#Binærobjekt - Eksempel: Et dokument eller et bilde
#Boolean - True eller false
#Liste - En liste av objekter

def nvdb2kart( sokeobjekt, lagnavn='FintKartlag'): 
    """
    Første spede begynnelse på nvdb2qgis. 
	
	Vil ta et søkeobjekt fra  nvdbapi-v2 biblioteket (nvdbFagdata eller nvdbVegnett) og hente 
	tilhørende data fra NVDB-api V2 innenfor QGIS-kartflatens utstrekniing 
	
	UMODENT: TODO
		- B
	
    Arguments: 
        sokeobjekt: Søkeobjekt fra nvdbapi.nvdbVegnett eller nvdbapi.nvdbFagdata
        objekter:list of dict En liste med dict som ser slik ut: 
            { 'egenskaper' [ 'id' : 1, 'beskrivelse' : 'Tekst'], 'wktgeom' : 'WKT-streng' }
            
            WKT - streng kan (inntil videre) være POINT eller LINESTRING. Bygger opp en generisk håndtering 
            stein for stein...
        

    Keywords: 
        lagnavn='FintKartlag' Navn på laget
 

	""" 
	
    if isinstance( sokeobjekt, nvdbFagdata): 
	
	
        punktlag = memlayerwrap( 'Point', 'field=id:integer&field=description:string', lagnavn) 
        linjelag = memlayerwrap( 'MultiLinestring', 'field=id:integer&field=description:string', lagnavn) 
        
		# Må nok ha mer 
		
    for feat in objekter: 
        if 'POINT' in feat['wktgeom']: 
            punktlag.addFeature(feat)
        elif 'LINESTRING' in feat['wktgeom']: 
            linjelag.addFeature(feat)
        else:
            print( 'Ukjent geometritype:', feat['wktgeom'])
    
    punktlag.ferdig()
    linjelag.ferdig()
 
    # # 274549,7042095


