"""
Klasser og funksjoner for å føye NVDB vegnett og fagdata til QGIS 3


"""
from qgis.core import QgsProject,  QgsVectorLayer, QgsFeature, QgsGeometry, QgsPoint, QgsLineString
from nvdbapi import nvdbVegnett, nvdbFagdata, nvdbFagObjekt, finnid


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
        
    def addFeature(self, egenskaper, wktgeometri):
        if not self.active:
            QgsProject.instance().addMapLayer(self.layer)
            self.layer.startEditing() 
            self.active = True 
        
        feat = QgsFeature()    
        feat.setAttributes( egenskaper )
        mygeom = QgsGeometry.fromWkt( wktgeometri )
        
        # Tricks for å tvinge 3d => 2d koordinater
        if 'Point' in self.geomtype:
            pass
            feat.setGeometry( QgsGeometry.fromPointXY( mygeom.asPoint()) )  
        elif 'Linestring' in self.geomtype: 
            pass
        elif 'Polygon' in self.geomtype:
            pass
        else: 
            print('Geomtype not supported', self.geomtype)
            # feat.setGeometry(  )
            
        success = self.layer.addFeature( feat )
        
        return( success ) 
        
    def ferdig( self): 
        if self.active: 
            self.layer.commitChanges()
            self.active = False
        
        
def lagQgisDakat(  sokeobjekt):
    """
    Lager attributt-definisjon for QGIS objekter ihht datakatalogen
    
    
    
    TODO: 
        DOKUMENTASJON
        fraDato, sistmodifisert skal være QGIS datoer, ikke tekst
        Behov for å fjerne visse tegn fra egenskapsnavn som QGIS bruker?
            f.eks &, : ?             
    
    """
    # Liste med ID'er for egenskapstypene for denne objekttypen  
    egIds = [] 
    # Liste med QGIS datatyper. Kort liste med metadata først, deretter matcher listen med egenskapstyper. 
    qgisEg = ['field=nvdbid:int', 'versjon:int', 'fraDato:string', 'sistmodifisert:string' ]

    for eg in sokeobjekt.objektTypeDef['egenskapstyper']: 
        egIds.append( eg['id'] ) 
        qgisEg.append( egenskaptype2qgis( eg) ) 
        
    
    qgisDakat = '&field='.join( qgisEg )
    
    return egIds, qgisEg, qgisDakat
        
def egenskaptype2qgis( egenskaptype): 
    """
    Omsetter en enkelt NVDB datakatalog egenskapdefinisjon til QGIS lagdefinisjon-streng

    Kan raffineres til flere datatyper. Noen aktuelle varianter
    
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
    
    
def nvdbFeat2qgisProperties( mittobj, egIds): 
    """
    Omsetter egenskapsverdiene pluss utvalgte metadata fra et 
    NVDB fagobjekt til en liste med QGIS verdier. 
    """ 
    qgisprops = [ mittobj.id, mittobj.metadata['versjon'], 
                 mittobj.metadata['startdato'], 
                 mittobj.metadata['sist_modifisert'] ]
    
    for eg in egIds: 
        
        qgisprops.append( mittobj.egenskapverdi(eg))
    
    return qgisprops



def nvdb2kart( sokeobjekt, lagnavn=None, geometritype='beste', 
                                        inkludervegnett='beste'): 
    """
    Første spede begynnelse på nvdb2qgis. 
	
	Vil ta et søkeobjekt fra  nvdbapi-v2 biblioteket (nvdbFagdata eller 
    nvdbVegnett) og hente tilhørende data fra NVDB-api V2 innenfor 
    QGIS-kartflatens utstrekniing 
	
	UMODENT: TODO
		- B
	
    Arguments: 
        sokeobjekt: Søkeobjekt fra nvdbapi.nvdbVegnett eller
                                                    nvdbapi.nvdbFagdata

    Keywords: 
        lagnavn=None Navn på kartlagetlaget 
            (default: "Vegnett" eller objekttypenavn )
        
        geometri=None eller en av ['egen', 'vegnett', 'flate', 'linje',  
                                                    'punkt', 'alle' ]
            Detaljstyring av hvilken egeongeometri-variant som 
            foretrekkes. Defaultverdien None returnerer den mest 
            "verdifulle" geometritypen som finnes
            etter den samme prioriteringen som Vegkart-visningen: 
                1. Egengeometri, flate
                2. Egengeometri, linje
                3. Egengeometri, punkt
                4. Vegnettgeometri
            'alle' betyr at vi viser ALLE egengeometriene til objektet 
            pluss vegnettsgeometri (hvis da ikke dette overstyres med 
            valget inkludervegnett='aldri')
                
        inkludervegnett='beste' | 'alltid' | 'aldri' 
            Default='beste' betyr at vi kun viser vegnettsgeometri hvis det 
                    ikke finnes egengeometri. 
                    (Tilsvarer geometritype="beste") 
            'alltid' :  Vis ALLTID vegnettsgeometri i tillegg til 
                        evt egeomgeometri(er) 
            'aldri'  :  Vis aldri vegnettsgeometri 
                        dette betyr at du ikke får noen representasjon
                        av objektet. Du mister altså informasjon 
 
        Noen av nøkkelordkombinasjonene kan altså 
        gi 0, 1 eller flere  visninger av samme objekt. Det vil si at 
        samme objekt blir til 0, 1, eller flere forekomster i  

	""" 
    
    # Kortform geometritype 
    gt = geometritype
        
    # Sjekker input data    
    gtyper = [ 'flate', 'linje', 'punkt', 'vegnett', 'alle' ]
    if gt and isinstance(gt, str ) and gt.lower() not in gtyper: 
        print( 'nvdb2kart: Ukjent geometritype angitt:', gt, 
            'skal være en av:', gtyper) 
        print( 'nvdb2kart: Setter geometritype=vegnett') 
        gt = 'vegnett'
        
    
    # Bruker datakatalog-navnet om ikke annet er angitt: 
    if not lagnavn: 
        lagnavn = sokeobjekt.objektTypeDef['navn']
	
    if isinstance( sokeobjekt, nvdbFagdata): 

		# Datakatalogdiefinisjon ihtt Qgis-terminologi 
        (egIds, qgisEg, qgisDakat ) = lagQgisDakat(sokeobjekt)
        
        punktlag = memlayerwrap( 'Point',           qgisDakat, str(lagnavn))
        multipunktlag = memlayerwrap( 'MultiPoint',           qgisDakat, str(lagnavn) + '_multi' )
        linjelag = memlayerwrap( 'Linestring', qgisDakat, str(lagnavn)) 
        multilinjelag = memlayerwrap( 'MultiLinestring', qgisDakat, str(lagnavn) + '_multi' ) 
        flatelag = memlayerwrap( 'Polygon',         qgisDakat, str(lagnavn))         
        multiflatelag = memlayerwrap( 'MultiPolygon',         qgisDakat, str(lagnavn) + '_multi') 
        collectionlag = memlayerwrap( 'GeometryCollection',         qgisDakat, str(lagnavn) + '_geomcollection') 
	
        mittobj = sokeobjekt.nesteNvdbFagObjekt()
        count = 0 
        while mittobj: 
            count += 1
            if count % 500 == 0 or count in [1, 10, 20, 50, 100]: 
                print( 'Lagt til ', count, 'av', sokeobjekt.antall, 'nvdb objekt i kartlag', lagnavn) 

            segmentcount = 0 
            # Qgis attributter = utvalgte metadata + egenskapverdier etter datakatalogen 
            egenskaper = nvdbFeat2qgisProperties( mittobj, egIds ) 
            
            # Flagg for å holde styr på hvordan det går med forsøk på å vise 
            # egengeometri
            beste_gt_suksess = False 

                            
            if gt in [ 'alle', 'flate', 'beste' ]: 
                pass
                
                
                # beste_gt_suksess = True
            elif gt in [ 'alle', 'linje' ] or (gt == 'beste' and not beste_gt_suksess): 
                pass 
                
                # beste_gt_suksess = True
            elif gt in ['alle', 'punkt' ] or (gt == 'beste' and not beste_gt_suksess): 
                pass

                # beste_gt_suksess = True                
            elif (gt== 'vegnett') or (inkludervegnett == 'alltid') or \
                            (gt == 'beste' and not beste_gt_suksess):
                pass                 
            
            else:
                # TODO Debug logikken, hva har vi glemt?  
                print( 'DEBUG! Viser ikke geometri for', mittobj.id, 'burde vi det?')
                print( 'Valgt geometritype=', gt) 
                print( 'Inkluder vegnett? =', inkludervegnett) 
            
            if not geometritype: 
                
                if mittobj.egenskapverdi( 'Geometri, flate')    and 'POLYGON' in mittobj.egenskapverdi( 'Geometri, flate'):
                    geometritype = 'flate'
                elif  mittobj.egenskapverdi( 'Geometri, linje') and 'LINESTRING' in mittobj.egenskapverdi( 'Geometri, linje'):
                    geometritype = 'linje'
                elif mittobj.egenskapverdi( 'Geometri, punkt')  and 'POINT' in mittobj.egenskapverdi( 'Geometri, punkt'): 
                    geometritype = 'punkt'
                else:
                    geometritype = 'vegnett' or (inkludervegnett == 'alltid') or ( ) 

                                        
            mygeom = mittobj.egenskapverdi( 'Geometri, ' + geometritype ) 
#             print( 'debug', mittobj.id, geometritype, mygeom) 
            
            
            # Bruker vegnett hvis angitt, eller hvis vi ikke fant 
            # den egengeometrivarianten vi helst vil ha
            if geometritype.lower() != 'vegnett' and mygeom:
                pass
#                print( 'debug', mittobj.id, 'bruker denna egengeometrien:', mygeom, geometritype )

            else:
                mygeom = mittobj.wkt() 
#               print( 'debug', mittobj.id, ': Bruker vegnettgeom', mygeom )
                # TODO må lage funksjon som itererer over vegnett-segmenter! 
                # Enten lager ett objekt per vegsegment, eller setter dem sammen til multiline-string... 
            
            if 'point' in mygeom[0:7].lower(): 
                punktlag.addFeature( egenskaper, mygeom )
            elif 'line' in mygeom[0:7].lower(): 
                linjelag.addFeature( egenskaper, mygeom)
            elif 'polygon' in mygeom[0:10]().lower():
                flatelag.addFeature( egenskaper, mygeom) 
            else:
                print( debug, mittobj.id, 'Ukjent geometritype:', feat.geometry())
    
            mittobj = sokeobjekt.nesteNvdbFagObjekt()
            # Slutt while-løkke 

        punktlag.ferdig()
        linjelag.ferdig()
        flatelag.ferdig()     
        multipunktlag.ferdig()
        multilinjelag.ferdig()
        multiflatelag.ferdig()
        collectionlag.ferdig()

        
        return punktlag, linjelag, flatelag   
        
