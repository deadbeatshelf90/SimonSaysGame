import serial
import time
import numpy as np
import firebase_admin
import threading
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("path to database key")
firebase_admin.initialize_app(cred,{'databaseURL': 'link to database'})

#game com port
ser = serial.Serial()
ser.baudrate = 115200
ser.port = "COM7"
ser.open()

#heartrate monitor com port
ser2 = serial.Serial()
ser2.baudrate = 115200
ser2.port = "COM4"
ser2.open()

#open the database and if it is empty make the branch sessions
ref = db.reference()
if ref.get() is None:
    ref.update({"sessions":""})
ref = db.reference().child('sessions')  #open the branch sessions



#find how many sessions have been played
ref1 = db.reference('sessions')
first_branch_data = ref1.get()
if first_branch_data:  #if there is past sessions in the database
    last_element_key = list(first_branch_data.keys())[-1]
    next_session = str(last_element_key)
    next_session = int(next_session[-1])  # get the number at the end of the final key eg. "session 2" will give 2
    next_session += 1
else:                  #if the database is empty then the next session will be session 1
    next_session = 1  

#list to gather heartrate(bpm) over each round
heartrates = []
def gameloop():
    #string to catch game data
    stringOut = ""
    while True:
        global next_session
        global heartrates
       #get the game data one character at a time
        game_data = ser.read().decode()
        
        #generate a string from the game data that ends at "#"
        if game_data == "#":
            stringOut += game_data
            ref = db.reference().child('sessions').child("session_" + str(next_session)) # used to name each session
            ref.update({"Round_" + str(stringOut[0]):{"Heartrates":heartrates,"Avg_heartrate":int(np.mean(heartrates)),"Result":str(stringOut[2:-1])}})
            #if the game is lost then the session is over
            if str(stringOut[2:-1]) == "loose":
                next_session += 1
            #clear stringOut for the next round
            stringOut = ""
            heartrate = []
        else:
            stringOut += game_data
            
def heartloop():
    global heartrates
    #string to catch heartrate data
    heartOut = ""
    timeCheck2 = 0
    while True:
        #get the heartrate one character at a time
        heart_data = ser2.read().decode()
        if heart_data == "#":
            print(heartOut)
            #validate that the heartrate data is an integer
            if heartOut.isdigit():
                heartOut = int(heartOut)
                #find the time difference between 2 peaks of the raw data graph
                if heartOut >= 750:
                    timeCheck1 = time.time()
                    timeCheckT = timeCheck1 - timeCheck2
                    timeCheck2 = timeCheck1
                    #use time difference to calculate beats per minute from raw data
                    bpm = timeCheckT * 60
                    bpm = int(bpm) #validates that bpm is an integer
                    if (bpm >= 50) and (bpm < 100):
                        heartrates.append(bpm)
            heartOut = ""
        else:
            heartOut += heart_data
        
threadGame = threading.Thread(target=gameloop)
threadHeart = threading.Thread(target=heartloop)

threadGame.start()
threadHeart.start()

threadGame.join()
threadHeart.join()