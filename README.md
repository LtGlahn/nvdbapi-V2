# Jobb interaktivt mot NVDB api V2 

Jobb interaktivt og objektorientert mot NVDB api V2! 

Les først gjennom [https://www.vegvesen.no/nvdb/apidokumentasjon](https://www.vegvesen.no/nvdb/apidokumentasjon)
for nyttige tips og innblikk i logikken. 

Rutinene håndterer all kommunikasjon mot NVDB API, inklusive paginering (d.v.s. vi henter passe
store "bøtter" med data av gangen) Du føyer til dine egne søkefiltere, og du kan sjekke antall 
treff før du laster ned data. 

Vi oppforder alle til å gi oss relevant kontaktinfo i form av http headere 
X-Client og X-Kontaktperson. Dermed har vi bedre statistikk over hvem som bruker API'et til hva, 
og kan også nå ut til brukerne ved problemer. Denne informasjonen lese fra fila 
*nvdbapi-clientinfo.json*; bruk gjerne malen  *nvdbapi-clientinfo-template.json* som utgangspunkt. 

Hovedrutinen *nvdbapi.py* skal fungere både med python 2 og 3. Et par av eksemplene er skrevet i python 3, men det aller meste er bakoverkompatibelt med python 2 (dog med litt mindre god håndtering av UTF-8, dvs norske tegn). 

## nvdbVegnett 

Klasse for å hente veglenker fra NVDB api. 

## nvdbFagdata(objektTypeId) 

Klasse for å hente fagdata (ikke vegnett, men øvrige data om vegen). Totalt har vi definert ca 385 ulike objekttyper
i [datakatalogen](https://www.vegvesen.no/nvdb/apidokumentasjon/#/get/vegobjekttyper). 

nvdbFagdata utvider klassen nvdbVegnett, og arver metoder og egenskaper fra denne. 

argumentet objektTypeID (heltall) angir hvilke objekttype vi jobber med, definert i [datakatalogen](https://www.vegvesen.no/nvdb/apidokumentasjon/#/get/vegobjekttyper)

# Felles metoder for nvdbVegnett og nvdbFagdata


### refresh() 

Sletter alle data, og nullstiller telleverket i paginering. 

### addfilter_geo( FILTER )

FILTER er en python dictionary med lokasjonsfilter (geografisk filter, områdefilter). 
Se [dokumentasjon](https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/lokasjonsfilter)

Merk at noen filter kun kan brukes for å hente fagdata, ikke vegnett. 

Eksempel

```
v = nvdbVegnett()
v.addfilter_geo( { 'kommune' : 1601 } )
v.addfilter_geo( { 'vegreferanse' : 'ev6hp15' } )
# Filteret har nå verdien { 'vegreferanse' : 'ev6hp15', 'kommune' : 1601 }
```

### nesteForekomst()

Gir deg ett NVDB objekt (vegnett eller fagdata), i henhold til dine søkekriterier (filtre). Alle detaljer med datanedlasting fra API håndteres internt. 


```
v = nvdbFagdata(807) # Døgnhvileplass
p = v.nesteForekomst()
while p: 
	print o['id']
	o = v.nesteForekomst()
```


### nestePaginering()

Bruker paginering til å neste "bøtte" med data fra NVDB forekomst, i henhold 
til alle dine søkekriterier (filtre). 

Returerer True hvis dette ga gyldige data, og False når vi har hentet alle objektene. 

Du må selv kopiere data over fra listen *data\[\'objekter\'\]*

 
```
p = nvdbFagdata( 809) # Døgnhvileplass 
p.paginering['antall'] = 3 # Jukser litt med antall forekomster per bøtte. 
TF = p.nestePaginering()
minliste = []
while TF: 
    minliste.extend( p.data['objekter'] )
	TF = p.nestePaginering()
```

# Flere metoder for nvdbFagdata

### nesteNvdbFagObjekt() 

Objektorientert tilnærming - returnerer neste forekomst av NVDB objektet som en instans av
klassen [nvdbFagObjekt](https://github.com/LtGlahn/nvdbapi-V2#nvdbfagobjekt)

### info()

Skriver til konsoll alle filtere og antall treff. 

### statistikk()

Sjekker hvor mange forekomster som finnes med angitte filtre. Returnerer dict med antall treff 
og  strekningslengde (antall meter). Strekningslengde er 0 for punktobjekter. 


### addfilter_egenskap( TEKSTSTRENG )

Tekststreng med filtre for egenskapsverdier. Se dokumentasjon for [egenskapsfiltre](https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/egenskapsfilter)

```
p = nvdbFagdata( 809) # Døgnhvileplass 
p.addfilter_egenskap( '9246=12886 AND 9273=12940') 
p.addfilter_egenskap()
>>  {'egenskap': '9246=12886 AND 9273=12940'} 
p.addfilter_egenskap( '' ) # Nullstiller filteret. 
```

### addfilter_overlapp( TEKSTSTRENG ) 

Henter fagdata som overlapper med annen objekttype (evt med eget filter). Se dokumentasjon for [overlappfilter](https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/overlappfilter)

```
u = nvdbFagdata(570) # Trafikkulykker
u.addfilter_overlapp( '105(2021=2738)') #  Trafikkulykker med fartsgrense = 80 km/t
```

### egenskaper( egenskapsTypeID):

Skriver ut definisjonen av angitt egenskapstype (ID, heltall). 
Hvis ingen ID oppgis skriver vi ut en liste med ID, navn og type
for alle egenskapstyper for denne objekttypen. 

I stedet for ID (heltall) kan du også oppgi en tekststreng som sjekkes mot 
navnet på egenskapstypene. 

Denne funksjonen er nyttig for å finne riktig verdi på egenskap- og overlappfiltere. 
```
p = nvdbFagdata( 809) # Døgnhvileplass 
p.egenskaper()
p.egenskaper(9270) # Vaskeplass for trailere
p.egenskaper( 'ask') # Fritekst-søk, matcher ID 9270
```



# Egenskaper nvdbVegnett og nvdbFagdata

Variabel | Verdi
---------| --------
data | Holder nedlastede data (i listen *objekter*) og metadata 
geofilter | Geografisk filter
headers | http headere som følger alle kall mot API
sisteanrop | Siste kall som gikk mot NVDB API 
objektTypeID | ID til objekttypen (ikke nvdbVegnett)
objektTypeDef | Datakatalogdefinisjon for objekttypen (ikke nvdbVegnett)
egenskapsfilter | Filter for egenskapsverdier (ikke nvdbVegnett)
overlappfilter | Filter for overlapp mot andre fagdata (ikke nvdbVegnett)
antall | Antall objekter i NVDB som tilfredsstiller kriteriene (ikke nvdbVegnett)
strekningslengde | Total lengde på objektene i NVDB som tilfredsstiller søkekriteriene (ikke nvdbVegnett)

# nvdbFagObjekt

Klasse for objektorientert behandling av fagdata. 

### egenskap( id_or_navn, empty=None)

Returnerer egenskapstype (dataverdi pluss metadata). Via nøkkelordet empty kan man angi ønsket retur hvis egenskapen ikke finnes. 

Argumentet _id_or_navn_ kan være heltall (datakatalog ID, mest skuddsikkert) eller (deler av) navnet på egenskapstypen. 

### egenskapverdi( id_or_navn, empty=None)

Som funksjonen "egenskap", men returnerer kun egenskapsverdien (selve dataverdien). 

eksempel:
```python
tunnellop = nvdbapi.nvdbFagdata(67)
ettLop = tunnellop.nesteNvdbFagObjekt()

# Henter egenskapen "Navn" for dette tunnelløpet
ettLop.egenskap('Navn')

# Henter kun egenskapsverdien 
ettLop.egenskapsverdi( 'Navn' )

# Bruker datakatalog ID i stedet for navn (mer skuddsikkert)
ettLop.egenskapsverdi( 1081 )

# Forkortelser eller deler av egenskapsnavnet er OK 
#(merk: Ingen sjekk på om frasen matcher flere egenskapsnavn, du får det første treffet)
ettLop.egenskap('MERK') # Gir første case *in*sensitive treff på frasen "merk" i egenskapsnavnet. 

# Angi at du vil ha tom streng (""), ikke None hvis egenskapstypen ikke finnes
# (Nei, vi sjekker ikke om dette er en lovlig egenskap for denne objekttypen etter datakatalogen)
tomStreng = ettLop.egenskapsverdi( 'finnes ikke', empty='')

```
### enumverdi( _id_or_navn, empty=None)
Som funksjonen "egenskapsverdi", men returnerer enmu_id - ikke dataverdien. Vil returnere None (eller din "empty"-verdi) 
hvis du bruker funksjonen på egenskaper som IKKE er enum (flervalg,tekst eller flervalg, tall). 

### wkt 

Returnerer koordinatene til objektets geometri som [Well Known Text](https://en.wikipedia.org/wiki/Well-known_text)

### relasjon(relasjon=None)

Returnerer en liste med alle relasjoner (default, uten argumenter), eller 
med nøkkelordet _relasjon=verdi_ returneres en liste med subsett
av relasjoner. Mulige verdier for nøkkeord _relasjon_ er _barn_, _foreldre_, 
_egenskapsID_ eller _egenskapsnavn_ til din favoritt objekttype. 

eksempel: 


```python
tunnellop = nvdbapi.nvdbFagdata(67)
ettLop = tunnellop.nesteNvdbFagObjekt()

# Henter mor-tunnellen, 3 ulike metoder
mor = ettLop.relasjon(relasjon='foreldre')
mor = ettLop.relasjon(relasjon='Tunnel')
mor = ettLop.relasjon(relasjon='581')

# Henter datterobjekt Tunnelportal, 
tp = ettlop.relasjon(relasjon='Tunnelport') # Delvis match
tp = ettlop.relasjon(relasjon='Tunnelportal') # Eksakt match
tp = ettlop.relasjon(relasjon=69)

# henter alle barn 
barn = ettlop.relasjon(relasjon='barn')

```


# TO DO 
======== 

 - [x] ~~Smart~~ håndtering av relasjoner. 
 - [x] Fiksa! ~~Litt snål oppførsel når du fyrer opp flere instanser av nvdbFagdata samtidig? Ser ut som om filtre og egenskapsverdier _"arves"_ fra den første instansen.~~  
 - [ ] Mere testing. 
 - [ ] Fikse på turistveg-eksemplet: Tynning av geometri + kun 2D koordinater. 
 
 
EKSEMPLER 
======

### turistveger2geojson

Leser NVDB fagdata 777 Turistveger og lagrer til GeoJson. 

> NB! Koordinatene burde vært tynnet for oversiktskart, ca 35mb totalt. Og vi får 3D koordinater, ikke helt sikker på hvor mange geojson-klienter som takler det like bra. 

### bomstasjoner-retninger.py

En litt i overkant pirkete test av innkrevingsretning for bomstasjoner. Vi sjekker om bomstasjonens egenskaper stemmer overens med dens vegtilknytning (der innkrevingsretning _*egentlig*_ bestemmes). Videre sjekker vi vegnettets orientering og metreringsretning. Til sist legger vi på kompassretning for den reelle innkrevingsretningen. 
