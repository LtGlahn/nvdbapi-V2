from nvdbapi import *
"""UFERDIG - eksempelkode, klipp-oglim"""


	
def dump_geojson( fagdata ):

		# raise NotImplementedError( 'Ikke implementert') 
		
		outdata = {   "type": "FeatureCollection",
					"features":  [] }
		
		forekomst = self.nesteForekomst()
		while forekomst: 
			geom = shapely.wkt.loads( forekomst['geometri']['wkt'] )
			properties = self.forekomst_egenskaper2sosinavn( forekomst) 
			gjsn = geojson.Feature(geometry=geom, properties=properties) 
			outdata['features'].append( gjsn) 
			forekomst = self.nesteForekomst()
			
		return outdata
		# Se https://gist.github.com/drmalex07/5a54fc4f1db06a66679e 
		

def forekomst_egenskaper2sosinavn( self, nvdbfagdataforekomst):
		if not self.objektTypeId: 
			raise ValueError( '\n'.join(('ObjektTypeID mangler.',  
									'\tEks: N = nvdbFagData(45)', 
									'\teller: N = nvdbFagData()',
									'       N.objektType(45)')))		

		jsonut = { }
		data = { } 
		for eg in self.objektTypeDef['egenskapstyper']: 
			jsonut.update( { eg['sosinavn'] : '' }  )
			data.update(  { eg['id'] : eg['sosinavn'] }  )

		nn = nvdbfagdataforekomst
		
		for egen in nn['egenskaper']: 
			mykey = data[egen['id']]
			jsonut[mykey] = egen['verdi']
			jsonut.update(  { 'ObjektId' : nn['id'] } ) 
		
		return jsonut
	

def fildump(filnavn, objekttype, kriterier='', format='json', pretty=True ): 
	"""Laster ned angitt objekttype fra NVDB api (i hht søkekriteriene)
	Laster (foreløbig) alle data inn i minnet før lagring til disk. 
	(Testes - blir det veldig ressurskrevende?). Kommentar på dette?
	""" 
	
	
	
	raise NotImplementedError('Not implemented yet!')