# hydroVallee.py
# Serveur pour le site d'information sur l'hydrométrie des rivières bretonnes.

import http.server
import socketserver
from urllib.parse import urlparse, parse_qs, unquote
import json

import matplotlib.pyplot as plt
import datetime as dt
import matplotlib.dates as pltd

import sqlite3

import os.path
#
# Définition du nouveau handler
#
class RequestHandler(http.server.SimpleHTTPRequestHandler):

  # sous-répertoire racine des documents statiques
  static_dir = '/client'

  #
  # On surcharge la méthode qui traite les requêtes GET
  #
  def do_GET(self):

    # On récupère les étapes du chemin d'accès
    self.init_params()
    
   
   
    if self.path_info[0] == 'stations':
      self.send_stations()
      
     # le chemin d'accès commence par /time
    elif self.path_info[0] == 'time':
      self.send_time()   
      
    elif self.path_info[0] == 'graphe':
      self.send_courbes() 
     
    else:
      
      self.send_static()


  #
  # On surcharge la méthode qui traite les requêtes HEAD
  #
  def do_HEAD(self):
    self.send_static()

  #
  # On envoie le document statique demandé
  #
  def send_static(self):

    # on modifie le chemin d'accès en insérant un répertoire préfixe
    self.path = self.static_dir + self.path

    # on appelle la méthode parent (do_GET ou do_HEAD)
    # à partir du verbe HTTP (GET ou HEAD)
    if (self.command=='HEAD'):
        http.server.SimpleHTTPRequestHandler.do_HEAD(self)
    else:
        http.server.SimpleHTTPRequestHandler.do_GET(self)
  
  #     
  # on analyse la requête pour initialiser nos paramètres
  #
  def init_params(self):
    # analyse de l'adresse
    info = urlparse(self.path)
    self.path_info = [unquote(v) for v in info.path.split('/')[1:]]  # info.path.split('/')[1:]
    self.query_string = info.query
    self.params = parse_qs(info.query)

    # récupération du corps
    length = self.headers.get('Content-Length')
    ctype = self.headers.get('Content-Type')
    if length:
      self.body = str(self.rfile.read(int(length)),'utf-8')
      if ctype == 'application/x-www-form-urlencoded' : 
        self.params = parse_qs(self.body)
    else:
      self.body = ''
   
    # traces
    print('info_path =',self.path_info)
    print('body =',length,ctype,self.body)
    print('params =', self.params)
    
  #
  # On envoie un document avec l'heure
  #
  def send_time(self):
    
    # on récupère l'heure
    time = self.date_time_string()

    # on génère un document au format html
    body = '<!doctype html>' + \
           '<meta charset="utf-8">' + \
           '<title>l\'heure</title>' + \
           '<div>Voici l\'heure du serveur :</div>' + \
           '<pre>{}</pre>'.format(time)

    # pour prévenir qu'il s'agit d'une ressource au format html
    headers = [('Content-Type','text/html;charset=utf-8')]

    # on envoie
    self.send(body,headers)

  #
  # On génère et on renvoie la liste des régions et leur coordonnées (version TD3)
  #
  def send_stations(self):

    conn = sqlite3.connect('Crepes.sqlite')
    c = conn.cursor()
    
    c.execute("SELECT X,Y,LbStationHydro,CdStationHydroAncienRef FROM 'Stations'")
    r = c.fetchall()
    #On vérifie que des données sur la station sont diponibles dans la table de données
    c.execute("SELECT DISTINCT code_hydro FROM 'hydro_historique'")
    ac = c.fetchall()  
    
    for i in range(len(r)):
        if (r[i][3],) in ac:
            r[i]+=(1,)
          #  print(r[i][3])
    
        else:
            r[i]+=(0,)
    
    headers = [('Content-Type','application/json')];
    body = json.dumps([{'nom':n, 'lat':lat, 'lon': lon, 'cd':cd, 'datAv': datAv} for (lon,lat,n,cd,datAv) in r])
    self.send(body,headers)


            
  def send_courbes(self):

    conn = sqlite3.connect('Crepes.sqlite')
    c = conn.cursor()
    anD=self.path_info[5]
    moisD=self.path_info[6]
    jourD=self.path_info[7]
    anF=self.path_info[8]
    moisF=self.path_info[9]
    jourF=self.path_info[10]
    cdeb=self.path_info[1]
    cmoy=self.path_info[2]
    cvf=self.path_info[3]
    cvF=self.path_info[4]
    
    fichier1 = 'courbes/'+cdeb+cmoy+cvf+cvF+self.path_info[11]+anD+moisD+jourD+anF+moisF+jourF+'.png'

    #Si le fichier est déjà présent, on ne recrée pas de nouveau graphe
    
    if os.path.isfile("client/"+fichier1):
        print("Image trouvée")
    else:
    
        d1="'{}-{}-{}'".format(anD,moisD,jourD) 
        d2="'{}-{}-{}'".format(anF,moisF,jourF) 
        
        if len(self.path_info) <= 1 or self.path_info[11] == '' :   # pas de paramètre => station par défaut
            station = [("J1711710","blue")]                         #pas utilisé en pratique parce qu'il s'agit de stations grisées
            self.path_info[11]="inconnu"
        else:
            # On teste que la région demandée existe bien
            c.execute("SELECT code_hydro FROM 'hydro_historique'")
            codes = c.fetchall()
            if (self.path_info[11],) in codes:   # Rq: codes est une liste de tuples
              station = [(self.path_info[11],"blue")]
            else:
                print ('Erreur nom')
                self.send_error(404)    # Station non trouvée -> erreur 404
                return None
            
        debit=bool(int(cdeb))
        moyenne=bool(int(cmoy))
        valeur_faible=bool(int(cvf))
        valeur_forte=bool(int(cvF))
    
       # boucle sur les régions
        for l in (station) :
            # configuration du tracé
            fig1 = plt.figure(figsize=(18,6))
            ax = fig1.add_subplot(111)
            #ax.set_ylim(bottom=0,top=10)
            ax.grid(which='major', color='#888888', linestyle='-')
            ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
            ax.xaxis.set_major_locator(pltd.YearLocator())
            ax.xaxis.set_minor_locator(pltd.MonthLocator())
            ax.xaxis.set_major_formatter(pltd.DateFormatter('%B %Y'))
            ax.xaxis.set_tick_params(labelsize=10)
            ax.xaxis.set_label_text("Date")
            
            if debit:
                caca='debit (m^3/s) '
                titre='Debit pour la station sélectionnée'
                ax.yaxis.set_label_text(l)
                plt.legend(loc='lower left')
                plt.title(titre,fontsize=16)
                
            
                code='"'+l[0]+'"'
                c.execute("SELECT  debit_donnee_validee_m3,date FROM (SELECT  debit_donnee_validee_m3,date FROM hydro_historique  WHERE code_hydro={}) WHERE date BETWEEN {} and {} ORDER BY date".format(code,d1,d2))  # ou (l[0],)
                r = c.fetchall()
                # recupération de la date (colonne 2) et transformation dans le format de pyplot
                x = [pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r if not a[0] == '']
                # récupération des débits (colonne 8)
                y = [float(a[0]) for a in r if not a[0] == '']
                # tracé de la courbe
                plt.plot(x,y,linewidth=1, linestyle='-', marker='o', color=l[1], label=l[0])
         
            if moyenne:
                caca='moyenne_interannuelle  '
                titre='Moyenne interannuelle pour la station sélectionnée'
                ax.yaxis.set_label_text(l)
                plt.legend(loc='lower left')
                plt.title(titre,fontsize=16)
                
                code='"'+l[0]+'"'
                c.execute("SELECT moyenne_interannuelle,date FROM (SELECT moyenne_interannuelle,date FROM hydro_historique  WHERE code_hydro={}) WHERE date BETWEEN {} and {} ORDER BY date".format(code,d1,d2))  # ou (l[0],)
                r2 = c.fetchall()
                x2=[pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r2 if not a[0] == '']
                # récupération des débits (colonne 8)
                z = [float(b[0]) for b in r2 if not b[0] == '']
                # tracé de la courbe
                
                plt.plot(x2,z,linewidth=1,linestyle='-',marker='o',label=l[0])
            
            if valeur_faible:
                caca='valeur_faible (m^3/s) '
                titre='Valeur_faible pour la station sélectionnée'
                ax.yaxis.set_label_text(l)
                plt.legend(loc='lower left')
                plt.title(titre,fontsize=16)
                
                code='"'+l[0]+'"'
                c.execute("SELECT valeur_faible,date FROM (SELECT valeur_faible,date FROM hydro_historique  WHERE code_hydro={}) WHERE date BETWEEN {} and {} ORDER BY date".format(code,d1,d2))  # ou (l[0],)
                r2 = c.fetchall()
                x2=[pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r2 if not a[0] == '']
                # récupération des  (colonne 8)
                z = [float(b[0]) for b in r2 if not b[0] == '']
                # tracé de la courbe
                plt.plot(x2,z,linewidth=1,linestyle='-',marker='o',label=l[0])
            
            if valeur_forte:
                caca='Valeur_forte (m^3/s) '
                titre='Valeur_forte pour la station sélectionnée'
                ax.yaxis.set_label_text(l)
                plt.legend(loc='lower left')
                plt.title(titre,fontsize=16)
                
                code='"'+l[0]+'"'
                c.execute("SELECT valeur_forte,date FROM (SELECT valeur_forte,date FROM hydro_historique  WHERE code_hydro={}) WHERE date BETWEEN {} and {} ORDER BY date".format(code,d1,d2))  # ou (l[0],)
                r2 = c.fetchall()
                x2=[pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r2 if not a[0] == '']
                # récupération des débits (colonne 8)
                z = [float(b[0]) for b in r2 if not b[0] == '']
                # tracé de la courbe
                
                plt.plot(x2,z,linewidth=1,linestyle='-',marker='o',label=l[0]) 
                
    
            # génération de la courbe de débit dans un fichier PNG
            
            plt.savefig('client/{}'.format(fichier1))
            plt.close()
            
        #html = '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
        body = json.dumps({
                'title': 'courbe'+self.path_info[11], \
                'img': '/'+fichier1 \
                 });
        # on envoie
        headers = [('Content-Type','application/json')];
        self.send(body,headers)
        
            
        
  def send(self,body,headers=[]):

    # on encode la chaine de caractères à envoyer
    encoded = bytes(body, 'UTF-8')

    # on envoie la ligne de statut
    self.send_response(200)

    # on envoie les lignes d'entête et la ligne vide
    [self.send_header(*t) for t in headers]
    self.send_header('Content-Length',int(len(encoded)))
    self.end_headers()

    # on envoie le corps de la réponse
    self.wfile.write(encoded)

 
#
# Instanciation et lancement du serveur
#bkjbb
httpd = socketserver.TCPServer(("", 8080), RequestHandler)
httpd.serve_forever()

