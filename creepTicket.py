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
import bs4
from prettytable import PrettyTable
import csv
import re

token_auth = '71c60729-1623-4e1e-b11f-5caf81aa9639'
url=""

init() #colorama init()

#convertir_en_temps:parse 20000101T000000 to 2000-01-01 00:00:00
def convertir_en_temps(chaine):
    return datetime.strptime(chaine.replace('T', ''), '%Y%m%d%H%M%S')

#convertir_en_verse: parse 2000-01-01-00-00-00 to 20000101T000000
def convertir_en_verse(chaine):
    return chaine[0:10].replace('-','')+"T"+chaine[10:].replace('-','')

#convertir_en_temps_bla: parse 2000-01-01 to 22/01/2017
def convertir_en_temps_bla(chaine):
    #chaine.replace('-','')
    rechaine = '{}/{}/{}'.format(chaine[-2:], chaine[5:7], chaine[:4])
    return rechaine

if __name__ == '__main__':
    #Parse argument
    arguments = docopt(__doc__, version='creepy Tickets 0.0.1')

    cov = arguments.get('--covoiturage')
    train = arguments.get('--train')

    #Option verification
    if not cov and not train:
        print("Please add options -t or -c.")
        quit()

    #print(from_statiom, to_station, date)

    #Url definition in according to opt -t or -c
    if train:
        from_statiom = station_uic.get(arguments['<from>'])
        to_station = station_uic.get(arguments['<to>'])

        #Verification of station inputs
        if from_statiom == None or to_station == None or \
            from_statiom == "None" or to_station == "None":
            print("Sorry, I didn't fine this stations UIC.")
            quit()
        #Valid time format
        if len(arguments['<date>']) == 19:
            date = convertir_en_verse(arguments['<date>'])
        elif len(arguments['<date>']) == 10:
            date = (arguments['<date>'])
        else:
            print("Time format input error, please retry.")
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

    city=[] #To store city's latitude and longitude
    city2 = []
    if cov:
        readData = csv.reader(open('cp-to-geo.csv', 'rU'), delimiter=';')
        from_statiom = arguments['<from>'].upper()
        to_station = arguments['<to>'].upper()
        date = convertir_en_temps_bla(arguments['<date>'])

        for line in readData:
            line[0] = ' '.join(line[0].split())
            if line[0]==from_statiom:
                city.append([line[0],line[1],line[2]])
            if line[0]==to_station:
                city2.append([line[0], line[1], line[2]])

        #print(city)
        #print(city2)
        url = 'https://www.blablacar.fr/trajets/{}/{}/#?fn={}&fc={}%7C{}&fcc=FR&tn={}&tc={}%7C{}'\
        '&tcc=FR&db={}&sort=trip_date&oder=asc&limit=10&page=2'\
        .format(city[0][0].lower(), city2[0][0].lower(),city[0][0].lower(), city[0][1], city[0][2], \
        city2[0][0].lower(), city[0][1], city[0][2], "22%2F01%2F2017")
        print(url)
        #https://www.blablacar.fr/trajets/strasbourg/nancy/#?db=c&fn=Strasbourg
        #&fc=48.5734053%7C7.7521113&fcc=FR&tn=Nancy&tc=48.692054%7C6.184417&tcc=FR&sort=trip_date&order=asc&limit=10&page=1
        try:
            bbcar = requests.get(url)
            soup = bs4.BeautifulSoup(bbcar.text, "lxml")
        except requests.exceptions.RequestException as e:
            print("Error {}".format(e))
            quit()
        else:
            exrp = re.compile('<[^>]+>')
            #list of name
            list_name = []
            for line in soup.body.find_all("h2", class_="ProfileCard-info ProfileCard-info--name u-truncate"):
                list_name.append(exrp.sub("",str(line).replace(' ','').replace('\n','')))

            #list of city from and to
            list_city_all = []
            list_city_from = []
            list_city_to = []
            for line in soup.body.find_all("span", "trip-roads-stop"):
                list_city_all.append(exrp.sub("", str(line).replace(' ', '')))
            i = 0
            for line in list_city_all:
                if i%2 is 0:
                    list_city_from.append(line)
                else:
                    list_city_to.append(line)
                i += 1

            #list of start time
            list_start_time = []
            for line in soup.body.find_all("h3","time light-gray"):
                tostring = exrp.sub("",str(line).replace('\n',''))
                list_start_time.append(tostring)

            #list of links
            list_links = []
            for line in soup.body.find_all("a", "trip-search-oneresult"):
                tmp = 'https://www.blablacar.fr{}'.format(line['href'])
                list_links.append(tmp)

            #list of Price
            list_price = []
            for line in soup.body.find_all("div", class_ = "price price-black"):
                list_price.append(exrp.sub("",str(line).replace(' ','').replace('\n','').replace('parplace','')))

            col = PrettyTable()
            col.add_column("Name", list_name)
            col.add_column("From", list_city_from)
            col.add_column("To", list_city_to)
            col.add_column("StartTime", list_start_time)
            col.add_column("Price", list_price)
            #col.add_column("Links", list_links)
            print(col)

    print(Fore.WHITE + "\n\n**Edited by Tearsyu**" + Fore.RESET)
