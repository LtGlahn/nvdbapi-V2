# -*- coding: utf-8 -*-
"""
Kommunikasjon mot NVDB api v3 LES og SKRIV

apiforbindelse - Klasse som håndterer alt det praktiske med 
innlogging mot NVDB api skriv eller les. 


""" 
import uuid
import getpass
import requests
import json
import copy 


class apiforbindelse( ):
    """
    Håndterer innlogging og kommunikasjon mot NVDB api LES og SKRIV .
    """
    
    def __init__( self, miljo='utvles' ):
        """
        Oppretter en instans av apiskrivforbindelse
        
        Arguments: 
            None 
        Keywords: 
            miljo: string, en av 
                    utvles
                    testles
                    prodles 
                    utvskriv
                    testskriv
                    prodskriv

                    (Kan droppes hvis den settes ved innlogging)
                
        """ 
        
        self.headers = {    
                            "X-Client" : "LtGlahn python", "User-Agent" : "LtGlahn python requests"
                              }
        self.tokenId = ''
        self.requestsession = requests.session()
        self.headers['X-Client-Session'] = str( uuid.uuid4() )
        self.velgmiljo( miljo=miljo)
        self.proxies = None
        # self.proxies =  {  "http": "http://proxy.vegvesen.no:8080", "https": "http://proxy.vegvesen.no:8080" }

    def velgmiljo( self, miljo='utvles'):

              
        if miljo == 'utvles': 
            self.apiurl = 'https://apilesv3.utv.atlas.vegvesen.no' 
            self.openAMurl = 'https://www.utv.vegvesen.no/openam/json/authenticate' 
            self.openAmNavn = 'iPlanetDirectoryProOAMutv'
            self.headers['Accept'] = 'application/vnd.vegvesen.nvdb-v3-rev1+json'
            self.proxies =  {  "http": "proxy.vegvesen.no:8080", "https": "proxy.vegvesen.no:8080" }

        elif miljo == 'testles': 
            self.apiurl = 'https://apilesv3.test.atlas.vegvesen.no' 
            self.openAMurl = 'https://www.test.vegvesen.no/openam/json/authenticate' 
            self.openAmNavn = 'iPlanetDirectoryProOAMTP'
            self.headers['Accept'] = 'application/vnd.vegvesen.nvdb-v3-rev1+json'
        
        elif miljo == 'prodles': 
            self.apiurl = 'https://apilesv3.atlas.vegvesen.no' 
            self.openAMurl = 'https://www.vegvesen.no/openam/json/authenticate' 
            self.openAmNavn = 'iPlanetDirectoryProOAM'
            self.headers['Accept'] = 'application/vnd.vegvesen.nvdb-v3-rev1+json'

        elif miljo == 'utvskriv':
            self.apiurl = 'https://www.utv.vegvesen.no' 
            self.openAMurl = 'https://www.utv.vegvesen.no/openam/json/authenticate' 
            self.openAmNavn = 'iPlanetDirectoryProOAMutv'
            self.headers['Accept'] = 'application/json'
            self.headers['Content-Type'] = 'application/json'

        elif miljo == 'testskriv': 
            self.apiurl = 'https://www.test.vegvesen.no' 
            self.openAMurl = 'https://www.test.vegvesen.no/openam/json/authenticate' 
            self.openAmNavn = 'iPlanetDirectoryProOAMTP'
            self.headers['Accept'] = 'application/json'
            self.headers['Content-Type'] = 'application/json'            
            
        elif miljo == 'prodskriv': 
            self.apiurl = 'https://www.vegvesen.no' 
            self.openAMurl = 'https://www.vegvesen.no/openam/json/authenticate'
            self.openAmNavn = 'iPlanetDirectoryProOAM'
            self.headers['Accept'] = 'application/json'
            self.headers['Content-Type'] = 'application/json'
            
        else:
            print( 'Miljø finnes ikke! utvles, utvskriv, testles, testskriv, prodles, prodskriv')

                              
    def login(self, miljo=None, username='jajens', pw=None, klient=None): 
        """
        Logger inn i api.
        
        Arguments: 
            None
            
        Keywords: 
            miljo : None eller string, en av 
                    utvles,   testles,   prodles
                    utvskriv, testskriv, prodskriv
            
        
        """
        
        if miljo: 
            self.velgmiljo( miljo=miljo)

        headers = self.SVVpassord( username=username, pw=pw )
        
        self.loginrespons = self.requestsession.post( url=self.openAMurl, 
                                        headers=headers, 
                                        params = { 'realm' : 'External', 
                                                'authIndexType' : 'module', 
                                                'authIndexValue' : 'LDAP'})
        
        if self.loginrespons.ok:
            temp = self.loginrespons.json()
            if 'tokenId' in temp.keys():
                
                self.headers['Cookie'] = self.openAmNavn + '= ' + temp['tokenId']
                
            else: 
                print( 'Fikk ikke logget på - ingen tokenId :(' )
                
        else: 
            print( "Fikk ikke logget på :( " )
    
        # Setter sporbarhet 
        if klient: 
            self.klientinfo(klient)

        self.headers['X-Client-Session'] = str( uuid.uuid4() )
        
    def loggut(self): 
        """
        Logger ut av skriveAPI.
        
        Arguments: 
            None 
        """ 
        
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
    
    def klientinfo( self, klientinfo):
        """
        Få bedre sporbarhet / enklere søk i skriveapi-GUI! 
        
        Via http headeren X-Client kan du angi noe som er unikt for det problemet
        du jobber med akkurat nå, f.eks. fikse bomstasjon-takster. 
        
        
        Endringssett-objektets egenskap headers['X-Client'] settes lik klientinfo
        
        Arguments: 
            klientinfo TEKST - det du vil hete! 
            
        Keywords: NONE
        
        Returns: NONE
            
        """
        self.headers['X-Client'] = str( klientinfo )
    
    def skrivtil( self, path, data, **kwargs): 
        """
        Poster data til NVDB api skriv.
        
        Arguments:
            path : URL, enten relativt til /apiskriv, eller fullstendig adresse
            
            data : Datastrukturen som skal postes. Enten json (default) 
                    eller xml (angis i så fall med content-argumentet ved 
                    opprettelse av endringssett-objektet, eller ved å sette 
                    manuelt 
                    endringsett.headers["Content-Type"] = 'application/xml')
                    
        Keywords: 
            Eventuelle nøkkelord-argumenter sendes til python request-modulen
        """
        
        if path[0:4] == 'http': 
            url = path
        else: 
            url = self.apiurl + path
        

        return self.requestsession.post( url=url, 
                                            proxies=self.proxies, 
                                            headers=self.headers, 
                                            json = data, **kwargs)
        
    def les( self, path, headers={}, **kwargs): 
        """
        Http GET requests til NVDB REST skriveapi
        
        Arguments:
            path : URL, enten relativt til /apiskriv, eller fullstendig 
            
        Keywords: 
            Eventuelle nøkkelord-argumenter sendes til python request-modulen
        """
        
        if path[0:4] == 'http': 
            url = path
        else: 
            url = self.apiurl + path

        # Kopierer self.headers og angitte headers over i ny dictionary. 
        myheaders = { **self.headers, **headers}

        """Leser data fra NVDB api"""
        return self.requestsession.get( url=url, 
                                       proxies=self.proxies,
                                       headers=myheaders, 
                                       **kwargs)
        
