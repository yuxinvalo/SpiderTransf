#!/usr/bin/env python3
# coding=utf-8
#python creepTicket.py -c(covoiturage)t(train)b(bus) from to date


"""Tickets creepy
Usage:
    creepTicket [-ctb] <from> <to> <date>

Options:
    -h,--help                       show help list
    -c,--covoiturage                covoiturage
    -t,--train                      train SNCF

Example:
    python3 creepTicket.py -t Nantes Lille 2016-10-01-20-30-00
    python3 creepTicket.py -t Colmar Nancy 2017-01-20
    python3 creepTicket.py -t 'Paris Est' Colmar 2016-12-20
"""

from docopt import docopt
import json
from datetime import datetime
from station_uic import station_uic
import requests
from colorama import init, Fore

token_auth = '71c60729-1623-4e1e-b11f-5caf81aa9639'
url=""

init() #colorama init()

#convertir_en_temps:parse 20000101T000000 to 2000-01-01 00:00:00
def convertir_en_temps(chaine):
    return datetime.strptime(chaine.replace('T', ''), '%Y%m%d%H%M%S')

#convertir_en_verse: parse 2000-01-01-00-00-00 to 20000101T000000
def convertir_en_verse(chaine):
    return chaine[0:10].replace('-','')+"T"+chaine[10:].replace('-','')



if __name__ == '__main__':
    #Parse argument
    arguments = docopt(__doc__, version='creepy Tickets 0.0.1')

    cov = arguments.get('--covoiturage')
    train = arguments.get('--train')

    #Option verification and Time format verification
    if not cov and not train:
        print("Please add options -t or -c.")
        quit()

    if len(arguments['<date>']) == 19:
        date = convertir_en_verse(arguments['<date>'])
    elif len(arguments['<date>']) == 10:
        date = (arguments['<date>'])
    else:
        print("Time format input error, please retry.")
        quit()

    #print(from_statiom, to_station, date)

    #Url definition
    if train:
        from_statiom = station_uic.get(arguments['<from>'])
        to_station = station_uic.get(arguments['<to>'])
        #Verification of station inputs
        if from_statiom == None or to_station == None or \
            from_statiom == "None" or to_station == "None":
            print("Sorry, I didn't fine this stations UIC.")
            quit()
        url = 'https://api.sncf.com/v1/coverage/sncf/journeys?'\
        'from=stop_area:OCE:SA:{}&to=stop_area:OCE:SA:{}&datetime={}'\
        .format(from_statiom, to_station, date)

    #Begin with error handle
    try:
        r = requests.get(url, auth=(token_auth, ''))
    except Exception:
        print("Sorry, an unexpected error occurred when I connect to api SNCF, please check your networking.")
        quit()
    else:
        list = []
        n=r.json()
        for i in n['links'][0:2]:
            inval=convertir_en_temps(i['href'][-15:-1])
            list.append(inval)

        print(Fore.YELLOW + '\nFrom {} to {}: \n-Departure time is {}\n-Arrival time is {}\n-Duration is {}'\
            .format(arguments['<from>'], arguments['<to>'], list[0], list[1]\
            , list[1] - list[0]))

        print(Fore.RED + "\nStation stop at:" + Fore.RESET)
        for i in n['journeys'][0]['sections'][1]['stop_date_times'] :
            if i['stop_point']['name'] != arguments['<from>'] or i['stop_point']['name'] != arguments['<to>']:
                print(Fore.RED + "-" +i['stop_point']['name'],
                convertir_en_temps(i['departure_date_time'])-convertir_en_temps(i['arrival_date_time']),"minutes d'arrêt")

        print(Fore.WHITE + "\n\n**Edited by Yuxin**" + Fore.RESET)
