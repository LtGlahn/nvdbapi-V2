# -*- coding: utf-8 -*-
"""
Kommunikasjon mot, og skriving til NVDB skriveapi

Det anbefales STERKT at utvikling foregår mot docker-instans av skriveapi. 
https://www.vegdata.no/2016/03/09/utviklerutgave-av-skrive-apiet-tilgjengelig-pa-docker-hub/


apiskrivforbindelse - Klasse som håndterer alt det praktiske med innlogging mot skriveapi. 
	Kan også brukes til å lese data fra øvrige endrepunkt (endringssett, låser m.m.)

endringssett - Klasse som håndterer alle steg i skriveprosessen: 
 - registrering
 - validering
 - startskriving
 - sjekkfremdrift 
 
Selve endringssettet - de data som skal skrives / endres / slettes / korrigeres / oppdateres - 
er en python-dict i endringssett.data  - attributten. 

Eksempler på endringssett finner du i /generator/ - endepunktet i docker-instans, 
evt https://www.vegvesen.no/nvdb/apiskriv/generator/

Endringssettet må ha en api-forbindelse. Denne instansieres med et kall til funksjonen 
tilkobling, med en instans av apiskrivforbindelse som argument. 

Eksempel: 
	endringssett.tilkobling(  apiskskriv )


Selve tilbobklingen lagres i attributten endringssett.forbindelse, og kan nås der. 

Eksempel: 
	endringssett.forbindelse.login( )
	
"""
import requests
import json
import getpass
import copy

class apiskrivforbindelse():
    
    def __init__( self, miljo='nvdbdocker', content='json'):
        
        self.headers = {  "Content-Type" : "application/json", 
                            "Accept" : "application/json", 
                            "X-Client" : "PythonNvdbskriv" 
                              }
                              
        if content== 'xml': 
            self.headers["Content-Type"] = 'application/xml'
                              
        self.proxies = {} 
        self.tokenId = ''
                              
    def login(self, miljo='nvdbdocker', proxies=False, username='jajens', 
              pw=None): 
        
        if miljo == 'nvdbdocker': 
            
            if proxies: 
                self.proxies = {'http': 'proxy.vegvesen.no:8080', 
                                'https': 'proxy.vegvesen.no:8080'} 

            
            self.apiurl = 'http://164.132.107.230:8080'
            bruker = 'root00'
            
            self.requestsession = requests.session()
            self.loginrespons = self.requestsession.post( url=self.apiurl + '/login', 
                                         proxies=self.proxies, 
                                         headers=self.headers, 
                                         data = { 'user-id' : bruker })
            
        else: 
            if miljo == 'utv': 
                self.apiurl = 'https://www.utv.vegvesen.no' 
                openAMurl = 'https://www.utv.vegvesen.no/openam/json/authenticate' 
                openAmNavn = 'iPlanetDirectoryProOAMutv'
            
            elif miljo == 'test': 
                self.apiurl = 'https://www.test.vegvesen.no' 
                openAMurl = 'https://www.test.vegvesen.no/openam/json/authenticate' 
                openAmNavn = 'iPlanetDirectoryProOAMTP'
                
                
            elif miljo == 'prod': 
                self.apiurl = 'https://www.vegvesen.no' 
                openAMurl = 'https://www.vegvesen.no/openam/json/authenticate'
                openAmNavn = 'iPlanetDirectoryProOAM'
                
            else:
                print( 'Miljø finnes ikke! utv, test eller prod - eller nvdbdocker')

            headers = self.SVVpassord( username=username, pw=pw )
            
            self.requestsession = requests.session()
            self.loginrespons = self.requestsession.post( url=openAMurl, 
                                         headers=headers, 
                                         params = { 'realm' : 'External', 
                                                 'authIndexType' : 'module', 
                                                 'authIndexValue' : 'LDAP'})
            
            if self.loginrespons.ok:
                temp = self.loginrespons.json()
                if 'tokenId' in temp.keys():
                    
                    self.headers['Cookie'] = openAmNavn + '= ' + temp['tokenId']
            
                else: 
                    print( 'Fikk ikke logget på - ingen tokenId :(' )
            else: 
                print( "Fikk ikke logget på :( " )
        
    def loggut(self): 
        
        if 'vegvesen' in self.apiurl: 
            self.debug = self.requestsession.get( self.apiurl + '/openam/UI/Logout') 
        else: 
            self.debug = self.requestsession.get( self.apiurl + '/logout')
        
    def SVVpassord( self, username=None, pw=None): 
        
        if not username: 
            username = input( 'Username: ' )
        if not pw: 
            pw = getpass.getpass( username+"'s Password: ")
        headers = copy.deepcopy( self.headers )
        headers['X-OpenAM-Username'] = username
        headers['X-OpenAM-Password'] = pw
        
        return headers
        
    def skrivtil( self, path, data): 
        """Poster data til NVDB api skriv"""
        
        if path[0:4] == 'http': 
            url = path
        else: 
            url = self.apiurl + path
        
        if self.headers['Content-Type'] == 'applcation/xml': 
            return self.requestsession.post( url=url, 
                                     proxies=self.proxies, 
                                     headers=self.headers, 
                                     data = data)
        elif self.headers['Content-Type'] == 'application/json': 
            return self.requestsession.post( url=url, 
                                    proxies=self.proxies, 
                                    headers=self.headers, 
                                    json = data)
        else: 
            print( "Sjekk CONTENT-TYPE på api-forbindelse objektet")
            return None
        
    def les( self, path, **kwargs): 
        """Http GET requests til NVDB REST skriveapi
        """
        
        if path[0:4] == 'http': 
            url = path
        else: 
            url = self.apiurl + path
        
        
        """Leser data fra NVDB api"""
        return self.requestsession.get( url=url, 
                                       proxies=self.proxies,
                                       headers=self.headers, 
                                       **kwargs)
        

    def checklock( self, endringsettID ): 
        """Python request kall for å sjekke låser for endringssett 
        
        Returnerer python requests objekt. 
        """
        url = self.apiurl + '/nvdb/apiskriv/kontrollpanel/data/locks'
        params  ={ 'blocking' : endringsettID }
        
        r = self.les( url, params=params )
        return r 
        
    def checklock_prettyprint( self, endringsettID, printheader=False):
        """Pen utskrift av låser som evt blokkerer endringssettet
        """
        r = self.checklock( endringsettID)
        locks = r.json()
        if len(locks) > 0: 
            if printheader:
                print( "lockId endringssettID username commonName origin time")
            for lock in locks: 
                print( lock['lockId'], endringsettID, lock['username'], lock['commonName'], 
                      lock['origin'], lock['time'] )
        else: 
            print( "No locks for", endringsettID)

class endringssett(): 
    
    def __init__(self, data ):
        self.data = data
        self.status = 'ikke registrert' 
        
        # Initialiser attributter med False 
        self.forbindelse = False
        self.minlenke = False
        self.startlenke = False
        self.kansellerlenke = False
        self.statuslenke = False
        self.fremdriftlenke = False 
        self.validertresultat = False
    
    def tilkobling( self, apiskriv): 
        """Den forbindelsen man skal bruke i kommunikasjon med NVDB api 
        apiskriv = en instans av apiskrivforbindelse 
        hvor man er aktivt logget inn i skriveapi
        """
        self.forbindelse = apiskriv
    
    def valider(self): 
        """Validerer et endringssett. Forutsetter innlogget tilkobling
        """
        
        if not self.forbindelse: 
            print( "Ingen aktiv forbindelse med NVDB api skriv")
            return 
            
        self.validertrespons = self.forbindelse.skrivtil( '/nvdb/apiskriv/rest/v2/endringssett/validator', self.data )
        if self.validertrespons.ok: 
            self.validertresultat = self.validertrespons.json()
            
    def finnvalideringsfeil(self): 
        if not self.validertresultat: 
            self.valider()
        else: 
            for ff in self.validertresultat['resultat']['vegObjekter']: 
                if ff['feil']: 
                    print( ff['feil'], ff['nvdbId'])
    
                    
    def finnskrivefeil(self, returnNvdbId=False): 
        b = self.sjekkstatus(returjson=True)
        nvdbid_feiler = []
        endringer = {}
        # datakeys = set( self.data.keys())
        # if 'delvisOppdater' in self.data.keys():
        harnvdbid =  { 'oppdater', 'delvisOppdater', 
                                   'korriger', 'delvisKorriger', 'slett' }
        bb = harnvdbid.intersection( set( self.data.keys()))
        if bb: 
            bb_str = bb.pop() # Henter tekst fra set - mengden. Skal kun være 1 - en 
            endringer = dict(( p['nvdbId'], p) for p in self.data[bb_str]['vegObjekter'])
        elif  'registrer' in self.data.keys(): 
            endringer = dict(( p['tempId'], p) for p in self.data['registrer']['vegObjekter'])
        else: 
            print( 'Funky... dette skulle IKKE skje, her er mine dict-oppslagsnøkler', 
                  self.data.keys())            


        print( "fremdrift:", b['fremdrift'])
        for ff in b['resultat']['vegObjekter']: 
            if ff['feil']: 
                nvdbid_feiler.append( ff['nvdbid'])
                print(' --- FEIL -- ' )
                print(ff['nvdbId'], ff['feil'] )
                print( 'endringssett:' )
                if endringer and str(ff['nvdbId']) in endringer.keys(): 
                    print( json.dumps(endringer[str(ff['nvdbId'])], indent=4) )
                else: 
                    print( "Fant ingen endringssett med NVDB id", ff['nvdbId'], '????')
                 
        if returnNvdbId: 
            return nvdbid_feiler
        
    def registrer(self): 
        """Registrerer et endringssett. Forutsetter innlogget tilkobling
        """
        
        if not self.forbindelse: 
            print( "Ingen aktiv forbindelse med NVDB api skriv" )
            return
        
        self.registrertrespons = self.forbindelse.skrivtil('/nvdb/apiskriv/rest/v2/endringssett', self.data )
        if self.registrertrespons.ok: 
            self.status = 'registrert' 
            
            # Plukker ut lenker for å gå videre med prosessen. 
            data = json.loads( self.registrertrespons.text ) 
            for rel in data: 
                if rel['rel'] == 'self': 
                    self.minlenke = rel['src']
                    
                if rel['rel'] == 'start': 
                    self.startlenke = rel['src']
                    
                if rel['rel'] == 'kanseller': 
                    self.kansellerlenke = rel['src']
                    
                if rel['rel'] == 'status':
                    self.statuslenke = rel['src']
                    
                if rel['rel'] == 'fremdrift': 
                    self.fremdriftlenke = rel['src']
        

        else: 
            print( 'Endringssett IKKE registrert')
            print( self.registrertrespons.text )
            
    def startskriving(self ): 
        """Forutsetter at endringsettet er registrert og at vi har en aktiv 
        (innlogget) forbindelse til NVDB api skriv"""
        
        if self.status != 'registrert': 
            print( "Kan ikke starte skriveprosess før endringssett er registrert!" )
            return 
        
        if not self.forbindelse: 
            print( "Ingen aktiv forbindelse med NVDB api skriv")
            return 
            
        if not self.startlenke: 
            print( "Noe har gått galt - ingen lenke til å starte skriveprosess" )
            return 
            
        self.startrespons = self.forbindelse.skrivtil( self.startlenke, self.data)
        if self.startrespons.ok: 
            self.status = 'startet'
        
        
    def sjekkstatus(self, returjson=False ): 
        """Sjekker status på endringssettet"""
        if self.status == 'ikke registrert':
            print( "Endringssettet er IKKE registrert hos NVDB api")
        else: 
            
            if self.status == 'registrert': 
                print( "Endringssett er registrert hos NVDB api, skriveprosess er ikke startet")
            elif self.status == 'startet': 
                print( "Skriveprosess startet i NVDB api, bruk funksjon sjekkfremdrift")
                
            b = self.forbindelse.les( self.statuslenke)
            self.statusrespons = b 
            if b.text in [ '"UTFØRT"', '"AVVIST"'] : 
                self.status = b.text.replace('"', '') # Fjerner dobbelfnutter... 
            if returjson: 
                return( b.json())
            else: 
                print( "http status:", str( b.status_code))
                print( b.text)

            
    def sjekkfremdrift(self , returdata=False): 
        """Sjekker fremdrift på skriveprosess NVDB api
        Nøkkelord returdata=True (default: False) returnerer teksten 
        vi får fra NVDB api, til bruk i dine funksjoner, f.eks for å itere over
        mange endringssett (lurt å dele opp i mindre biter, pga låsekonflikt etc)
        Sjekk for verdien BEHANDLES i din applikasjon - det betyr at 
        skriveprosess ikke er ferdig behandlet. """
        if self.status == 'ikke registrert':
            returdata = "Endringssettet er IKKE registrert hos NVDB api"
            print( returdata )
        elif self.status == 'registrert':
            returdata = "Endringssettet registrert hos NVDB api, men" + \
                    " skriveprosess er ikke startet\n" +\
                    "Bruk funksjon startskriving for å starte skriveprosess" 
            print(returdata)
        else: 
            
            self.fremdriftrespons = self.forbindelse.les( self.fremdriftlenke)
            print( 'Http status:', self.fremdriftrespons.status_code)
            returdata = self.fremdriftrespons.text 
            print( returdata )
            
            self.status = returdata
        
        if returdata: 
            return returdata

    


