#!/c/Python/python.exe
# -*-coding:utf-8 -*

""" PROJET DE PPC: MAISON ET ENERGIE """

import threading
from multiprocessing import Process, Value, Lock, Queue
import time
import random
import signal
import os
import multiprocessing
import sysv_ipc
import sys
from termcolor import colored
from tkinter import * #interface graphique

lockR = threading.Lock()
lockE = threading.Lock()

response = open("event.txt", 'w')
request = open("request.txt", 'w')

#interface graphique Prix:
fenetrePrix = Tk()
fenetrePrix.title("Prix du Marche")
liste = Listbox(fenetrePrix, width=50, height=10)
liste.pack(side=TOP)
buton = Button(fenetrePrix, text="Quit", command=fenetrePrix.destroy)
buton.pack(side=BOTTOM)

t = " --- Bienvenue sur le marché ! Visualisez ici l'actualisation du "
t2 = "prix de l'energie et des facteurs dont il dépend. ---"
liste.insert(END,t)
liste.insert(END,t2)



#-----------------------------------------------------------------------------------------------
#--------------------------------- EXTERNAL PROCESS --------------------------------------------
#the signal handler: à chaque signal correspond un évènement
def handler(sig,frame):
	ttl = random.randint(1, 3) # generate a time to live
	if sig == 30:
	    t = str(sig)+" Le gouvernement s'est fait gilet jauné."
	    events[sig]=ttl
	elif sig == 10:
	    t= str(sig)+" Nils a cassé les tuyaux de gaz, ah bah bravo Nils."
	    events[sig]=ttl
	elif sig == 16:
	    t= str(sig)+" Il fait froid, le gaz est devenu solide, #physics."
	    events[sig]=ttl
	elif sig == 31:
	    t= str(sig)+" Changement de gouvernement."
	    events[sig]=ttl
	elif sig == 12:
	    t= str(sig)+" La Russie à augmenté le prix du Gaz."
	    events[sig]=ttl
	elif sig == 17:
	    t= str(sig)+" Le Gouvernement combat contre la surconsomation de gaz: augmentation du prix."
	    events[sig]=ttl
	lockE.acquire()
	with open("event.txt", "a+") as file:
		file.write(t + "\n")
		file.close()
	lockE.release()

# to associate the handler with each kind of signal
signal.signal(30,handler)
signal.signal(10,handler)
signal.signal(16,handler)
signal.signal(31,handler)
signal.signal(12,handler)
signal.signal(17,handler)


#array of events
#la clé est le numéro du signal mais représente aussi
#le coeficient de l'evenement dans l'equation
events = {} #(mutex peut etre)
run=True

def externalChild():
    print("Starting process: External")
    start = time.time()
    while True:
        end = time.time()
        if (end - start >= 10): #à chaque 10 secondes on rentre dans la boucle
            element = random.randint(1, 10)
            #if element between 1-6: an event happens
            #we send a diferent signal for each event
            if element == 1:
                os.kill(os.getppid(),30)
            elif element == 2:
                os.kill(os.getppid(),10)
            elif element == 3:
                os.kill(os.getppid(),16)
            elif element == 4:
                os.kill(os.getppid(),31)
            elif element == 5:
                os.kill(os.getppid(),12)
            elif element == 6:
                os.kill(os.getppid(),17)
                
            start=time.time() #reset timer

#-------------------------------------------------------------------------------------------------
#-------------------------------------- PRICE THREAD --------------------------------------------- 
   
#Ceci est le thread Price qui sert à calculer le prix de l'Energie
def price():
    global events
    global liste
    global run
    print("Starting thread: Price ", threading.current_thread().name)
    start = time.time()
    influence_event=0

    while run:
        end = time.time()
        if (end - start >= 5):#chaque cinq secondes on actualise le prix
            influence_event =0 #on reset l'influence de l'event
            copie_events = events.copy()
            #On calcule l'influence de External
            for sig in copie_events:
                ttl = events[sig]
                if ttl ==0:
                    #on supprimr l'evenement si son ttl est nul
                    events.pop(sig)
                    influence_event = influence_event - sig
                else:
                    #on reduit le ttl de chaque evenement avant le prochain passage dans la boucle
                    events[sig] = ttl -1
                    #on calcule la contribution des events dans le Prix
                    influence_event = influence_event + sig
            
            
            #On calcule l'influence de Weather
            t0="- La temperature est: " + str(temp.value) + " degrés"        
            liste.insert(END,t0)

            #long term attenuation coefficient
            y = 0.1
            #internal factors
            a = -3 #weather coef (+ il fait froid + c'est cher)
            b = 0.2   #demande
            c = 2 #aleatoire

            #equation du Prix de l'energie (in shared memory à faire)
            Energy_Price.value = y*Energy_Price.value + a / temp.value + b*Demand.value  + c*influence_event

            #interface graphique
            t1= "- La demande est: " + str(b*Demand.value)
            liste.insert(END,t1)

            t2= "- L'influence des evenements aleatoire est: " + str(c*influence_event)
            liste.insert(END,t2)

            t3="- L'influence du temps est: " + str(a*temp.value)
            liste.insert(END,t3)
     
            t4=" ------ Le prix est: "+ str(Energy_Price.value)+" euros  ------ "
            liste.insert(END,t4)

            t5 = " ------   Fin du jour   ------ "
            liste.insert(END,t5)
            liste.insert(END," ")
            
            liste.update()
            fenetrePrix.update()
            
            start= time.time() 
	       
    print("Thread Price terminé")            
            
#-----------------------------------------------------------------------------------------------
#-------------------------------------- WEATHER PROCESS ----------------------------------------
def weatherProcess(temp):
	print("Starting Process : Weather")
	start = time.time()
	while True:
		end = time.time()
		if(end-start >=15): #chaque 15 secondes nous changeons la température selon une loi aléatoire gaussienne 
			#la temperature est stocké dans une shared memory
			temp.value = random.gauss(15,20)
			start= time.time()

#----------------------------------------------------------------------------------------------
#-------------------------------------- HOME PROCESS ------------------------------------------
def homeProcess(Response_Queue, ID_House, nomfichier):
	print("Starting Process : Home")	
	
	housePolicy = random.randint(1,3) #la house policy est determiné aléatoirement à chaque création de processus maison
	#initialsation de la message queue
	#on envoie un premier message
	m = "1"
	Response_Queue.send(m.encode(), type = ID_House)
	
	while True:
		time.sleep(10)
		prodRate = random.uniform(1,5)
		consRate = random.uniform(1,5)
		EnergyFromMarket, ID = Response_Queue.receive(type = ID_House)
		stock = float(EnergyFromMarket.decode())
		NewEnergy = stock*prodRate - stock*consRate

		t0 = "Energie de la maison: " + str(NewEnergy) + "\n"
		
		#on a surplus d'energie: on envoie un message au market pur qu'il traite notre demande, en fonction de la house policy		
		if(NewEnergy >= 0):
			message = [housePolicy, 0.5*NewEnergy , ID_House]
			t= "REQUEST: J'ai un surplus d'energie. Ma house policy est " + str(housePolicy)+ ".\n"
		else:
			
			#on a un besoin d'energie, on tente d'en trouver gratuitement, on adresse un message de recherche de donneurs au market 
			if (NewEnergy < 0 and NewEnergy > -100): 
				message = [4, -1.5*NewEnergy, ID_House]
				t="REQUEST: J'ai besoin d'energie gratuite." + "\n"
					
			#si on a vraiment besoin, on achete directement
				
			else:
				message = [5, -1.5*NewEnergy, ID_House]
				t ="REQUEST : J'achète de l'energie."+ "\n"
				
				
		#print("je met "+ str(message[1]) + "dans la mesage queue des request")
		lockR.acquire()
		
		with open(nomfichier, "a+") as file:
			file.write("Maison " + str(ID_House) + "  ----- Nouvelles demande: ----- \n" + t + t0 +"\n\n\n")
			file.close()
		lockR.release()
		Request_Queue.put(message)
					
#------------------------------------------------------------------------------------------------
#----------------------------------Thread Transaction---------------------------------------

def message(Request_Queue, Response_Queue,Demand):
	global run
	print("Starting Thread: Lecture des messages :", threading.current_thread().name)
	# une semaphore modelise le nombre de donneurs disponibles
	giver = threading.Semaphore(0)
	# une semaphore modelise le nombre d'acquereurs disponibles
	taker = threading.Semaphore(0)
	# on limite à 3 le nombre de transactions se lancant simultanément
	max_trans = threading.Semaphore(3)
	while run:
		with max_trans:
			message_rcvd =  Request_Queue.get()
			trans = threading.Thread(target=transaction, args=(taker, giver, Request_Queue, Response_Queue, message_rcvd,Demand))
			trans.start()

	for i in range(15):	
		giver.release()
		taker.release()
	print("Thread message terminé")	

#-----------------------------------------------------------------------------
def transaction(taker, giver, Request_Queue, Response_Queue, message_rcvd,Demand ):
	ID_House = message_rcvd[2]


	#cas 1 = surplus d'energie avec house policy numero 1 = je vends toujours
	if (message_rcvd[0] == 1):
		message = message_rcvd[1]
		print(colored("RESPONSE : J'ai vendu mon surplus d'energie", "blue"), ID_House)
		Demand.value = Demand.value + message # message est négatif, la demande diminue
	
	



	#cas 2 = surplus d'energie avec house policy numero 2 = je donne si il y a un donneur
	elif (message_rcvd[0] == 2): 
		#on incremente de 1 le giver, on autorise l'acces a 1 personne de plus
		giver.release()
		start = time.time();
		while True:
			end = time.time()
			if (end - start < 3) : #pendant 3 secondes
				if (taker._value > 0 ): #si il y a un taker on donne
					message = message_rcvd[1]
					print(colored("RESPONSE HP2 : J'ai donné mon surplus d'energie.", "green"), ID_House)
					break;
			else:
				#il n'y a personne a donner, on redonne l'energie a la maison
				message = message_rcvd[1] 
				print(colored("RESPONSE HP2 : Je n'ai trouvé personne à qui donner, donc je garde mon energie. ", "yellow"), ID_House)
				break;
		
		giver.acquire() #on actualise qu'il n'y a un donneur de moins - on decremente la sem donneur
		time.sleep(1)





	#cas 3 = surplus d'energie avec house policy numero 3 = je donne si il y a un donneur, sinon je vends		
	elif (message_rcvd[0] == 3): 
		#on a un donneur supplementaire

		#giver.value = giver.value +1
		giver.release()
		start = time.time();
		while True:
			end = time.time()
			if (end - start < 3) : 
				if (taker._value > 0 ):
					#on donne
					message = message_rcvd[1]
					print(colored("RESPONSE HP3 : J'ai donné mon surplus d'energie. ", "green"), ID_House)
					break;
			else:
				#on a attendu 3 secondes et il n'y a personne a donner, on vends l'energie
				message = message_rcvd[1]
				
				print(colored("RESPONSE HP3: Je n'ai trouvé personne à qui donner, donc je vends mon energie. ", "yellow"), ID_House)
				Demand.value = Demand.value + message #msg negatif, on baisse la demande
				break;
		giver.acquire() 
		time.sleep(1)




	#cas 4 = besoin d'energie = je cherche un donneur		
	elif (message_rcvd[0] == 4):
		taker.release()
		
		# quelqu'un attend un donneur
		start = time.time();
		while True:
			end = time.time()
			if (end - start < 3) : #chaque 3 secondes
				#if giver.value > 0: #on vérifie si il a un donneur
				if (giver._value > 0 ):
					#j'ai trouve un donneur
					message = message_rcvd[1]
					print(colored("RESPONSE : J'ai trouve un donneur. ", "magenta"), ID_House)
					break;

			else : #sinon on indique qu'on n'a pas trouvé de donneur
				message = message_rcvd[1]
				print(colored("RESPONSE : Je n'ai trouvé personne pour me donner. ", "magenta"), ID_House)
				break;

		taker.acquire()
		time.sleep(1)
			
		
	#cas 4 = besoin d'energie = j'achète
	elif (message_rcvd[0] == 5):
		message = message_rcvd[1]
		print("J'ai acheté de l'energie. ______ ", ID_House )
		Demand.value = Demand.value + message #message positif, on augmente la demande

	Response_Queue.send(str(message).encode(), type = ID_House)




#------------------------------------------------------------------------------------------------
#--------------------------------------------------MAIN MARKET----------------------------------    
#ceci sera dans le MARKET
if __name__ == "__main__":
    
    #we start Home process - de 0 à 5

    Request_Queue = multiprocessing.Queue() #une seule
    #Response_Queue = multiprocessing.Queue() #une par process home
    key = 1
    Response_Queue= sysv_ipc.MessageQueue(key,sysv_ipc.IPC_CREAT)
    # Response_Queue = [ multiprocessing.Queue for i in range (autant que de homes)]
    
    
    Demand = Value('d',500.0)
    pHomes = [Process(target=homeProcess, args=(Response_Queue, i+1, str(i)+".txt"))for i in range (5)]
    for process in pHomes:
        process.start()

    #we create a limited number of thread, each one handling one demand from one house
    
    threadMessage = threading.Thread(target=message, args=(Request_Queue, Response_Queue,Demand))
    threadMessage.start()
    #PB: selon notre logique il faut autant de Response Queue que de  Home (les lock sont mal utilisées, nous n'avons pas de la programation parrallèle)
    


    #we start Weather process  
    temp = Value('d', 20.0)
    pWeather = Process(target=weatherProcess, args=(temp,))    
    pWeather.start()

    #we start the EXTERNAL process
    pExternal = Process(target=externalChild, )
    pExternal.start()
    
    #we start the Price thread
    Energy_Price = Value('d',0.0)
    threadPrice = threading.Thread(target=price, )
    threadPrice.start()


    fenetrePrix.mainloop()

    #apres la fermeture de la fenetre, on termine les threads et processus
    pWeather.terminate()
    run=False
    time.sleep(10)
    for process in pHomes:
        process.terminate()
 
    Response_Queue.remove()
    pExternal.terminate()
    
    os.kill(os.getpid(),9)
    os.kill(os.getpid(),4)
    os.kill(os.getpid(),17)
    os.kill(os.getpid(),22)
    os.kill(os.getpid(),21)
    os.kill(os.getpid(),3)
    os.kill(os.getpid(),18)



    

    
    

