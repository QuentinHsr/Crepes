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
    
    # le chemin d'accès commence par /debit_moyenne
    if self.path_info[0] == 'debits_moyennes':
      self.send_debits_moyennes(False,False,True)
   
    elif self.path_info[0] == 'stations':
      self.send_stations()
      
     # le chemin d'accès commence par /time
    elif self.path_info[0] == 'time':
      self.send_time()    
      
      # le chemin d'accès commence par /debit

      
    elif self.path_info[0] == 'debits':
      self.send_debits_moyennes(True,False,False)
      
    # le chemin d'accès commence par /moyennes
    elif self.path_info[0] == 'moyennes':
      self.send_debits_moyennes(False,True,False)
      
    # ou pas...
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
            print(r[i][3])
    
        else:
            r[i]+=(0,)
    
    headers = [('Content-Type','application/json')];
    body = json.dumps([{'nom':n, 'lat':lat, 'lon': lon, 'cd':cd, 'datAv': datAv} for (lon,lat,n,cd,datAv) in r])
    self.send(body,headers)


            
  def send_debits_moyennes(self,debit,moyenne,debit_moyenne):

    conn = sqlite3.connect('Crepes.sqlite')
    c = conn.cursor()
    
    if len(self.path_info) <= 1 or self.path_info[1] == '' :   # pas de paramètre => liste par défaut
        # Definition des régions et des couleurs de tracé
#        regions = [("Rhône Alpes","blue"), ("Auvergne","green"), ("Auvergne-Rhône Alpes","cyan"), ('Bourgogne',"red"), 
#                   ('Franche Comté','orange'), ('Bourgogne-Franche Comté','olive') ]
        station = [("J1711710","blue")]
        self.path_info[1]="inconnu"
    else:
        # On teste que la région demandée existe bien
        c.execute("SELECT code_hydro FROM 'hydro_historique'")
        codes = c.fetchall()
        if (self.path_info[1],) in codes:   # Rq: codes est une liste de tuples
          station = [(self.path_info[1],"blue")]
        else:
            print ('Erreur nom')
            self.send_error(404)    # Station non trouvée -> erreur 404
            return None
   
    if debit:
    
    
        # configuration du tracé des débits
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
        ax.yaxis.set_label_text("débit")
                
        # boucle sur les régions
        for l in (station) :
            c.execute("SELECT debit_donnee_validee_m3,date FROM 'hydro_historique' WHERE code_hydro=? ORDER BY date",l[:1])  # ou (l[0],)
            r = c.fetchall()
            # recupération de la date (colonne 2) et transformation dans le format de pyplot
            x = [pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r if not a[0] == '']
            # récupération des débits (colonne 8)
            y = [float(a[0]) for a in r if not a[0] == '']
            # tracé de la courbe
            plt.plot(x,y,linewidth=1, linestyle='-', marker='o', color=l[1], label=l[0])
            
    
        # génération de la courbe de débit dans un fichier PNG
        fichier1 = 'courbes/debits_'+self.path_info[1] +'.png'
        plt.savefig('client/{}'.format(fichier1))
        plt.close()
        
        #html = '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
        body = json.dumps({
                'title': 'Debit Station '+self.path_info[1], \
                'img': '/'+fichier1 \
                 });
        # on envoie
        headers = [('Content-Type','application/json')];
        self.send(body,headers)
      
         # légendes
        plt.legend(loc='lower left')
        plt.title("Débits de l'eau débit de lait",fontsize=16)
        
        
    if moyenne:
   
        # configuration du tracé des moyennes
        fig2= plt.figure(figsize=(18,6))
        ax = fig2.add_subplot(111)
        #ax.set_ylim(bottom=0,top=10)
        ax.grid(which='major', color='#888888', linestyle='-')
        ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
        ax.xaxis.set_major_locator(pltd.YearLocator())
        ax.xaxis.set_minor_locator(pltd.MonthLocator())
        ax.xaxis.set_major_formatter(pltd.DateFormatter('%B %Y'))
        ax.xaxis.set_tick_params(labelsize=10)
        ax.xaxis.set_label_text("Date")
        ax.yaxis.set_label_text("moyenne_interannuelle")
        
         # boucle sur les régions
        for l in (station) :
            c.execute("SELECT moyenne_interannuelle,date FROM 'hydro_historique' WHERE code_hydro=? ORDER BY date",l[:1])  # ou (l[0],)
            r = c.fetchall()
            # recupération de la date (colonne 2) et transformation dans le format de pyplot
            x = [pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r if not a[0] == '']
            # récupération des débits (colonne 8)
            y = [float(a[0]) for a in r if not a[0] == '']
            # tracé de la courbe
            plt.plot(x,y,linewidth=1, linestyle='-', marker='o', color=l[1], label=l[0])
        
        # génération de la courbe de la moyenne dans un fichier PNG
        fichier2 = 'courbes/moyenne'+self.path_info[1] +'.png'
        plt.savefig('client/{}'.format(fichier2))
        plt.close()
    
        #html = '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
        body = json.dumps({
                'title': 'Moyenne interannuelle '+self.path_info[1], \
                'img': '/'+fichier2 \
                 });
        # on envoie
        headers = [('Content-Type','application/json')];
        self.send(body,headers)
      
      
          # légendes
        plt.legend(loc='lower left')
        plt.title("Moyenne interannuelle",fontsize=16)
        
    if debit_moyenne:
               # configuration du tracé des moyennes
        fig3= plt.figure(figsize=(18,6))
        ax = fig3.add_subplot(111)
        #ax.set_ylim(bottom=0,top=10)
        ax.grid(which='major', color='#888888', linestyle='-')
        ax.grid(which='minor',axis='x', color='#888888', linestyle=':')
        ax.xaxis.set_major_locator(pltd.YearLocator())
        ax.xaxis.set_minor_locator(pltd.MonthLocator())
        ax.xaxis.set_major_formatter(pltd.DateFormatter('%B %Y'))
        ax.xaxis.set_tick_params(labelsize=10)
        ax.xaxis.set_label_text("Date")
        ax.yaxis.set_label_text("moyenne_interannuelle_et_debit")
        
         # boucle sur les régions
        for l in (station) :
            c.execute("SELECT debit_donnee_validee_m3,date FROM 'hydro_historique' WHERE code_hydro=? ORDER BY date",l[:1])  # ou (l[0],)
            r1 = c.fetchall()
            # recupération de la date (colonne 2) et transformation dans le format de pyplot
            x1 = [pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r1 if not a[0] == '']
            # récupération des débits (colonne 8)
            y = [float(a[0]) for a in r1 if not a[0] == '']
            
        
            c.execute("SELECT moyenne_interannuelle,date FROM 'hydro_historique' WHERE code_hydro=? ORDER BY date",l[:1])  # ou (l[0],)
            r2 = c.fetchall()
            x2=[pltd.date2num(dt.date(int(a[1][:4]),int(a[1][5:7]),int(a[1][8:]))) for a in r2 if not a[0] == '']
            # récupération des débits (colonne 8)
            z = [float(b[0]) for b in r2 if not b[0] == '']
            # tracé de la courbe
            plt.plot(x1,y,linewidth=1, linestyle='-', marker='o', color=l[1], label=l[0])
            plt.plot(x2,z,linewidth=1,linestyle='-',marker='o',color='red',label=l[0])
        
        # génération de la courbe de la moyenne dans un fichier PNG
        fichier3 = 'courbes/debitmoyenne'+self.path_info[1] +'.png'
        plt.savefig('client/{}'.format(fichier3))
        plt.close()
    
        #html = '<img src="/{}?{}" alt="ponctualite {}" width="100%">'.format(fichier,self.date_time_string(),self.path)
        body = json.dumps({
                'title': 'Moyenne interannuelle_et_debit '+self.path_info[1], \
                'img': '/'+fichier3 \
                 });
        # on envoie
        headers = [('Content-Type','application/json')];
        self.send(body,headers)
      
      
          # légendes
        plt.legend(loc='lower left')
        plt.title("Moyenne interannuelle et débit",fontsize=16)
      
  # On envoie les entêtes et le corps fourni
  #
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

