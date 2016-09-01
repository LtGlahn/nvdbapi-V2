# -*- coding: utf-8 -*-

import json
import requests
from warnings import warn

# Uncomment to silent those unverified https-request warnings
requests.packages.urllib3.disable_warnings() 

"""Den aller første starten på bibliotek for å hente data fra NVDB api V2 (og senere versjoner)"""

class nvdbVegnett: 
	"""Klasse for spørringer mot NVDB for å hente vegnett. 
	Jobber dynamisk mot NVDB api for å hente statistikk, laste ned data etc.
	Holder alle parametre som inngår i dialogen med NVDB api. 

	Grovt sett skal vi ha disse komponentene / funksjonene: 
		- Enkle metoder for å sette søkekriterier
		(geografisk filter) 
		
		- Smart utnyttelse av NVDB api'ets pagineringsfunksjon. 
			- Liste med objekter man kan iterere over
			- Hent neste "batch" med objekter 
			- Hent hvert enkelt objekt

	n = nvdbVegnett() 
	v = n.nesteForekomst()
	while v: 
		print v['id']  # Gjør noe spennende
		v = n.nesteForekomst()

	"""
	
	geofilter = {}
	headers = 	{ 'accept' : 'application/vnd.vegvesen.nvdb-v2+json', 
						'X-Client' : 'nvdbapi.py',
						'X-Kontaktperson' : 'Anonymous'}
	
	paginering = { 'antall' 		: 1000, 	# Hvor mange obj vi henter samtidig.
							
							'hvilken' 		: 0, 	# iterasjon 
													# i det lokale datasettet 
													# Dvs i+1 til 
													# array self.data['objekter'] 
													# 
							'meredata'		: True, # Gjetning på om vi kan hente mere data
							'initielt'		: True # Initiell ladning av datasett
				} 
	
	data = { 'objekter' : []}
	
	def __init__( self):
		
		self.update_http_header()


	def nestePaginering(self):
		""" = True | False. Blar videre til neste oppslag (side) i pagineringen.
		Nyttig for dem som selv vil kopiere / iterere over listen av objekter, 
		som holdes i attributten nvdbFagdata.data 
		Returnerer True eller False
		
		Eksempel
			n = nvdbFagdata( 45) # bomstasjon
			suksess = n.nestePaginering()
			while suksess: 
				mycopy = n.data['objekter']
				for bomst in mycopy:
					print bomst['id'] # Gjør noe spennende. 
				suksess = n.nestePaginering()
		"""
		if isinstance( self, nvdbFagdata) and not self.objektTypeId: 
			raise ValueError( '\n'.join(('ObjektTypeID mangler.',  
									'\tEks: N = nvdbFagData(45)', 
									'\teller: N = nvdbFagData()',
									'       N.objektType(45)')))
		if isinstance( self, nvdbFagdata) and not self.antall: 
			self.statistikk()
		
		if self.paginering['initielt']: 
		
			if isinstance( self, nvdbFagdata): 
				parametre = merge_dicts( 	self.geofilter, 
											self.overlappfilter, 
											self.egenskapsfilter, 
											self.respons, 
						{ 'antall' :  self.paginering['antall'] } )
				self.data = self.anrope( '/'.join(('vegobjekter', str(self.objektTypeId) )), 
					parametre=parametre ) 
					
			elif isinstance( self, nvdbVegnett): 
				parametre = merge_dicts( self.geofilter, 
						{ 'antall' : self.paginering['antall'] } )
				self.data = self.anrope( 'vegnett/lenker', parametre=parametre )

			self.paginering['initielt'] = False

			if self.data['metadata']['antall'] > 0: 
				return True
			else: 
				self.paginering['meredata'] = False
				return False
				
		elif self.paginering['meredata']:
			self.data = self.anrope( self.data['metadata']['neste']['href'] ) 
			
			if self.data['metadata']['returnert'] > 0: 
				return True
			else: 
				self.paginering['meredata'] = False
				return False
		
		else: 
			return False
		
	def nesteForekomst(self, debug=False): 
		"""Returnerer en enkelt forekomst av objekttypen. 
		Brukes for å iterere over mottatte data uten å bekymre seg 
		om evt paginering.
		Eksempel: 
			n = nvdbFagdata(45)
			bomst = n.nesteForekomst()
			while bomst: 
				print bomst.id # Gjør noe spennende med dette enkeltobjektet
				bomst = n.nesteForekomst()
		"""
		if isinstance( self, nvdbFagdata) and not self.objektTypeId: 
			raise ValueError( '\n'.join(('ObjektTypeID mangler.',  
									'\tEks: N = nvdbFagData(45)', 
									'\teller: N = nvdbFagData()',
									'       N.objektType(45)')))
		if isinstance( self, nvdbFagdata) and not self.antall: 
			self.statistikk()

		antObjLokalt = len(self.data['objekter'])
		if debug: 
			print( "Paginering?", self.paginering) 
		if self.paginering['initielt']: 
		
			if isinstance( self, nvdbFagdata): 
				parametre = merge_dicts( 	self.geofilter, 
											self.overlappfilter, 
											self.egenskapsfilter, 
											self.respons, 
						{ 'antall' :  self.paginering['antall'] } )
				self.data = self.anrope( '/'.join(('vegobjekter', str(self.objektTypeId) )), 
					parametre=parametre ) 
					
			elif isinstance( self, nvdbVegnett): 
				parametre = merge_dicts( self.geofilter, 
						{ 'antall' : self.paginering['antall'] } )
				self.data = self.anrope( 'vegnett/lenker', parametre=parametre )

			self.paginering['initielt'] = False

			if self.data['metadata']['antall'] > 0: 
				self.paginering['hvilken'] = 1
				return self.data['objekter'][0]
			else: 
				self.paginering['meredata'] = False
				return None
				
		elif self.paginering['meredata'] and self.paginering['hvilken'] > antObjLokalt-1: 
			self.data = self.anrope( self.data['metadata']['neste']['href'] ) 
			self.paginering['hvilken'] = 1
			
			if self.data['metadata']['returnert'] > 0: 
				return self.data['objekter'][0]
			else: 
				self.paginering['meredata'] = False
				return None
		
		elif self.paginering['meredata']: 
		
			self.paginering['hvilken'] += 1
			return self.data['objekter'][self.paginering['hvilken']-1]

		
	def addfilter_geo(self, *arg):
		"""Get or set GEO filters to your search. 
		Input argument is a dict with area- or road network filter, which are 
		appended to existing values. 

		
		See 
		https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/lokasjonsfilter 
		for a list of possible values. 
		
		Example 
		p = nvdb.nvdbFagdata(809)
		p.addfilter_geo( { 'vegreferanse' : 'Ev39' }
		p.addfilter_geo( { 'fylke' : [3,4] }
		p.addfilter_geo() # Returns the current value of this filter 
		
		addfilter_geo with no arguments returns the current filter. 
		
		Input empty dict {} or string to clear all GEO - filters
		
		""" 
		
		if len( arg) == 1: 
			if isinstance( arg[0], dict) and arg[0]: 
				self.geofilter.update( arg[0]) 
			elif isinstance( arg[0], dict) and not arg[0]: 
				self.geofilter = {} 
			elif isinstance( arg[0], str): 
				self.geofilter = {} 

			else:
				warn('Wrong input to addfilter_geo. Should be dict') 
		else:
			return self.geofilter

	def anrope(self, path, parametre=None, debug=False): 
	
		api = 'https://www.vegvesen.no/nvdb/api/v2/'
		if not api in path: 
			url = ''.join(( api, path)) 
		else: 
			url = path 
		r = requests.get(url, params=parametre, headers=self.headers)
		
		self.sisteanrop = r.url
		
		if debug:
			print( r.url[33:]) # DEBUG
		
		
		if r.status_code == requests.codes.ok:
			data = r.json()
			if debug and 'metadata' in data.keys(): 
				print( '\n',  data['metadata'], '\n' ) 
			return r.json()
		else:
			raise Exception('Http error: '+str(r.status_code) +' '+r.url +
							'\n' + r.text )
							
	def refresh(self):
		"""Deletes all data, resets pagination to 0"""
		self.paginering['hvilken'] = 0
		self.paginering['initielt'] = True
		self.paginering['meredata'] = True
		self.data =  { 'objekter' : []}
	
	

	def update_http_header(self, filename='nvdbapi-clientinfo.json'): 
	
		contactsfile = 'nvdbapi-clientinfo.json'
		# Http header info
		try: 
			with open(filename) as data_file:    
				contacts = json.load(data_file)

			if isinstance( contacts, dict): 
				self.headers = merge_dicts( self.headers, contacts) 

				if 'X-Client' not in contacts.keys(): 
					warn(' '.join(('No X-Client defined in ', filename )) ) 
					
				if 'X-Kontaktperson' not in contacts.keys(): 
					warn(' '.join(('No X-Contact defined in ', filename)) ) 

			else: 
				warn( 'X-Client and X-Contact not updated')
				warn( ''.join(( 'Tror ikke ', filename, 
							' har riktig struktur', '\nSe dokumentasjon')) )
				
		except IOError:
			print( '---')
			mytext = ' '.join( ('\nYou should provide the file', 
							contactsfile,  '\n',   
					'\n{ "X-Client" : "YOUR SYSTEM",\n', 
					'"X-Kontaktperson" : "ola.nordmann@eposten.din" }\n' ))
			warn( mytext ) 
			print( '---')



class nvdbFagdata(nvdbVegnett): 
	"""Klasse for spørringer mot NVDB ang en spesifikk objekttype. 
	Jobber dynamisk mot NVDB api for å hente statistikk, laste ned data etc.
	Holder alle parametre som inngår i dialogen med NVDB api. 

	Grovt sett skal vi ha disse komponentene / funksjonene: 
		- Enkle metoder for å sette søkekriterier
		(geografisk filter, egenskapsfilter m.m.) 

		- Enkle metoder for å hente, lagre og inspisere alle NVDB fagdata
		som tilfreddstiller søkekriteriene. 
		
		- Smart utnyttelse av NVDB api'ets pagineringsfunksjon. 
			- Liste med objekter man kan iterere over
			- Hent neste "batch" med objekter 
			- Hent hvert enkelt objekt

		- Statistikk for dette søket  

	n = nvdb() # Tomt objekt, klart til å få verdi
	n = nvdb(45) # Objekttypen er nå satt lik 45 (Bomstasjon) 
	n.addfilter_egenskap( '1820>=20') 
	
	# EKSEMPEL: Iterer over alle bomstasjoner
	n = nvdbFagdata(45) 
	bomst = n.nesteForekomst()
	while bomst: 
		print bomst['id']  # Gjør noe spennende
		bomst = n.nesteForekomst()

	"""
	
	
	
	def __init__( self, objTypeID):

		# Tomme datafelt
		self.objektTypeId = None
		self.objektTypeDef = None
		self.antall = None
		self.strekningslengde = None
		self.geofilter = {}
		self.egenskapsfilter = {}
		self.overlappfilter = {} 
		

		# Standardverdier for responsen
		self.respons  = { 'inkluder' :  ['alle'], # Komma-separert liste
							'srid' : 32633, 
							'geometritoleranse' : None, 
							'' : True
						}
		
		# Leser verdier for http header fra JSON-fil
		self.update_http_header()
		
		# Refresh er lurt, (arver tilstand fra andre instanser). 
		self.refresh()

		# Leser typedefinisjon fra NVDB api
		self.objektTypeDef = self.anrope( '/'.join(( 'vegobjekttyper', 
											str(objTypeID))) )
		self.objektTypeId = objTypeID 

	def statistikk(self): 
		if self.objektTypeId: 
		
			parametre = self.allfilters() 
			stat = self.anrope( '/'.join(('vegobjekter', str(self.objektTypeId), 
							'statistikk')), parametre=parametre  )  
			self.antall = stat['antall'] 
			self.strekningslengde = stat['strekningslengde'] 
			return stat
			
		else: 
			self.antall = None
			self.strekningslengde = None
			return { 'antall' : None, 'strekningslengde' : None }


	def info(self): 
		if self.objektTypeId: 
			print( 'ObjektType:', 
				str(self.objektTypeId), self.objektTypeDef['navn'] )
	
		else: 
			print( 'Ikke definert noen objekttype ennå') 
			print( 'Bruk: x = nvdbFagdatID) eller\n', ' x = nvdbFagdata()\n', 
					'x.objektType(ID)\n', 
					'hvor ID er objekttypens ID, eks bomstasjon = 45\n\n') 
	
		print( 'Filtere')
		print( json.dumps( self.allfilters(), indent=4))
		print( 'Parametre som styrer responsen:' ) 
		print( json.dumps( self.respons, indent=4))
		print( 'Statistikk') 
		print( json.dumps( self.statistikk(), indent = 4))


	def egenskaper(self, *arg):
		"""Skriver ut definisjonen av angitt egenskapstype (ID, heltall). 
		Hvis ingen ID oppgis skriver vi ut en liste med ID, navn og type
		for alle egenskapstyper for denne objekttypen. 
		"""

		if len(arg) == 0: 
			for eg in self.objektTypeDef['egenskapstyper']:
				print( eg['id'], eg['navn'], eg['datatype_tekst'] )
				
		else: 
			for eg in self.objektTypeDef['egenskapstyper']:
				if eg['id'] == arg[0] or str(arg[0]) in eg['navn']: 
					print( json.dumps( eg, indent=4)) 
		
		
	def allfilters( self): 
		"""Returns a dict with all current filters""" 
		return merge_dicts( self.geofilter, self.egenskapsfilter, 
						self.overlappfilter) 
		
	def addfilter_overlapp( self, *arg): 
		"""Get or set overlapp filters to your search. 
		Input argument is a text string with overlapp ilters, which is added to 
		existing filter. 
		NB! If you want to add to an EXISTING filter, care must be taken to 
		construct valid expressions using AND, OR and (if needed) parantheses. 

		
		See 
		https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/overlappfilter
		for explanation. 
		
		Example 
		p = nvdb.nvdbFagdata(570) # Trafikkulykke
		p.addfilter_overlapp( '67'  ) # Trafikkulykke in tunnels (tunnelløp)
		p.addfilter_overlapp( '105(2021=2738)'  ) # Ulykke where speed limit =80
		
		p.addfilter_overlapp( '' ) # Clears all values
		
		addfilter_overlapp with no arguments returns the current filter. 
		
		Input empty string to clear the filter
		
		""" 
		
		
		if len( arg) == 1 and arg[0]: 
			self.overlappfilter.update( { 'overlapp' : arg[0] } ) 
		elif len(arg) == 1 and not arg[0]: 
			self.overlappfilter = {} 
		else:
			return self.overlappfilter

		
	def addfilter_egenskap( self, *arg): 
		"""Get or set property filters (egenskapsfilter) to your search. 
		Input argument is a text string with property filters, which is added to 
		existing filter. 
		NB! If you want to add to an EXISTING filter, care must be taken to 
		construct valid expressions using AND, OR and (if needed) parantheses. 

		
		See 
		https://www.vegvesen.no/nvdb/apidokumentasjon/#/parameter/egenskapsfilter
		for explanation. 
		
		Example 
		p = nvdb.nvdbFagdata(45)
		p.addfilter_egenskap( '1820=20'  ) # takst = 20 kr
		p.addfilter_egenskap( 'OR 1820=50'  ) # is now "1820=20 OR 1820=50"
		
		p.addfilter_egenskap( '' ) # Clears all values
		
		addfilter_egenskap with no arguments returns the current filter. 
		
		Input empty string to clear the filter
		
		""" 
		
		
		if len( arg) == 1 and arg[0]: 
			self.egenskapsfilter.update( { 'egenskap' : arg[0] } ) 
		elif len(arg) == 1 and not arg[0]: 
			self.egenskapsfilter = {} 
		else:
			return self.egenskapsfilter



def merge_dicts(*dict_args):
	"""
	Python < 3.5 kompatibel kode for å slå sammen to eller flere dict. 
	Given any number of dicts, shallow copy and merge into a new dict,
	precedence goes to key value pairs in latter dicts.
	Sakset fra http://stackoverflow.com/questions/38987/
		how-can-i-merge-two-python-dictionaries-in-a-single-expression
	"""
	result = {}
	for dictionary in dict_args:
		result.update(dictionary)
	return result
