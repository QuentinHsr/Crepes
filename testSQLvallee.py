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

conn = sqlite3.connect('Crepes.sqlite')
c = conn.cursor()

c.execute("SELECT X,Y,LbStationHydro,CdStationHydroAncienRef FROM 'Stations'")
r = c.fetchall()
#On vérifie que des données sur la station sont diponibles dans la table de données
c.execute("SELECT DISTINCT code_hydro FROM 'hydro_historique'")
ac = c.fetchall()    
compt=0
for i in range(len(r)):
    if (r[i][3],) in ac:
        r[i]+=(1,)
        print(r[i][3])

    else:
        r[i]+=(0,)
        
headers = [('Content-Type','application/json')];
body = json.dumps([{'nom':n, 'lat':lat, 'lon': lon, 'cd':cd, 'datAv': datAv}\
                   for (lon,lat,n,cd,datAv) in r])