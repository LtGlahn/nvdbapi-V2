# -*- coding: utf-8 -*-
"""
Keeps credentials away from github and other public repos. 

Created on Mon Jan 16 10:06:50 2017

@author: jajens
"""
import json


def credentials():
    """Returns login info: { "yoursystem" : { "user" : "foo", "pw" : "baa" }}""" 

    mycredfile = '../credentials.json' 
    cred = {  "yoursystem" : { 
                              "user" : "foo", 
                              "pw" : "baa"
                          }
                }
    try: 
        with open(mycredfile) as cf: 
            tmp = json.load( cf) 
        
        # python 2 merge dict operation 
        # overwriting the data found here. 
        # http://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression
        z = cred.copy()
        z.update(tmp)
        return z 
    except FileNotFoundError:
        print( 'Could not load credentials file:' + mycredfile )
        return cred
                

