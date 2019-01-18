# -*- coding: utf-8 -*-
"""
Created on Sun Dec 30 14:00:30 2018

@author: cosme
"""
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as pltd

import sqlite3
import os.path
conn = sqlite3.connect('Crepes.sqlite')
c = conn.cursor()

#c.execute("SELECT X,Y,LbStationHydro,CdStationHydroAncienRef FROM 'Stations'")
#r = c.fetchall()
##On vérifie que des données sur la station sont diponibles dans la table de données
#c.execute("SELECT DISTINCT code_hydro FROM 'hydro_historique'")
#ac = c.fetchall()    
#compt=0
#for i in range(len(r)):
#    if (r[i][3],) in ac:
#        r[i]+=(1,)
#        print(r[i][3])
#
#    else:
#        r[i]+=(0,)
#        
#headers = [('Content-Type','application/json')];
#body = json.dumps([{'nom':n, 'lat':lat, 'lon': lon, 'cd':cd, 'datAv': datAv}\
#                   for (lon,lat,n,cd,datAv) in r])




#d1="'{}-{}-{}'".format('2018','01','04') 
#d2="'{}-{}-{}'".format('2018','01','10')
#
#c.execute("SELECT debit_donnee_validee_m3,date FROM (SELECT debit_donnee_validee_m3,date FROM hydro_historique  WHERE code_hydro=?) WHERE date BETWEEN {} and {} ORDER BY date".format(d1,d2),("'J1711710'",))  # ou (l[0],)
#r = c.fetchall()
            
fichier1 = 'courbes/debits_'+'J93006112017090120180901'+'.png'
if os.path.isfile("client/"+fichier1):
    print("Image trouvée")
else:
    print("Image non trouvée")
    
fichier1 = 'courbes/debits_'+self.path_info[1]+anD+moisD+jourD+anF+moisF+jourF+'.png'

#Si le fichier est déjà présent, on ne recrée pas de nouveau graphe

if os.path.isfile("client/"+fichier1):
    print("Image trouvée")
else:













