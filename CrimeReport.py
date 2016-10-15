import logging
logging.basicConfig(level=logging.DEBUG)
from spyne import Application, rpc, ServiceBase, \
    Integer, Unicode
from spyne import Iterable
from spyne.decorator import srpc
from spyne.protocol.http import HttpRpc
from spyne.protocol.json import JsonDocument
from spyne.server.wsgi import WsgiApplication
import requests
import operator

class CrimeReportService(ServiceBase):
    @srpc(Unicode, Unicode, Unicode, _returns=Iterable(Unicode))
    def checkcrime(lat, lon, radius):
        Crimes = requests.get("https://api.spotcrime.com/crimes.json?lat=" + lat + "&lon=" + lon + "&radius=" + radius + "&key=.").json()
        mostDengerousStreets = [] #a list to sotre the most dengerous streets

        totalCrime=0 #declaring variable to keep track of time the total no of crimes

        # declaring variables to keep track ow time window of the crime
        firstSlot = 0 #12:01am-3am crime counter
        secondSlot = 0 #3:01am-6am crime counter
        thirdSlot = 0 #6:01am-9am crime counter
        fourthSlot = 0 #9:01am-12noon crime counter
        fifthSlot = 0 #12:01pm-3pm crime counter
        sixthSlot = 0 #3:01pm-6pm crime counter
        seventhSlot = 0 #6:01pm-9pm crime counter
        eigthSlot = 0 #9:01pm-12midnight crime counter

        crimeType = {} # a dictionary to store all the crimes and values as their count of occurence.
        streets={} # a dictionary to store all the streets with keys as the streeet names and values as their count of occurence.

        for crime in Crimes["crimes"]: #iterating through each crime in the Crimes dictionary
            totalCrime = totalCrime + 1

            # Retrieving crime type and stroring it in the crimeType{} dictionary with its count of occurance:
            if crime['type'] in crimeType:
                crimeType[crime['type']] += 1
            else:
                crimeType[crime['type']] = 1

            #Retrieving street name from the complete address and stroring it in the steets{} dictionary:
            address = crime['address']
            if (address.find(" BLOCK OF ") > 0):
                address = address.split("OF ")
                if address[1] in streets:
                    streets[address[1]] += 1
                else:
                    streets[address[1]] = 1
            elif (address.find(" & ") > 0):
                address = address.split(" & ")
                if address[0] in streets:
                    streets[address[0]] += 1
                else:
                    streets[address[0]] = 1
                if address[1] in streets:
                    streets[address[1]] += 1
                else:
                    streets[address[1]] = 1
            elif (address.find(" BLOCK ") > 0):
                address = address.split(" BLOCK ")
                if address[1] in streets:
                    streets[address[1]] += 1
                else:
                    streets[address[1]] = 1
            elif (address.find(" BLOCK BLOCK ") > 0):
                address = address.split(" BLOCK BLOCK ")
                if address[1] in streets:
                    streets[address[1]] += 1
                else:
                    streets[address[1]] = 1
            else:
                if address in streets:
                    streets[address] += 1
                else:
                    streets[address] = 1

            # getting the crime time
            hour = int(crime['date'][9:11])
            minute = int(crime["date"][12:14])
            ampm = crime["date"][15:17]

            if (((hour == 12 and minute!=0) or (hour>=1 and hour < 3)) or (hour == 3 and minute == 0)):
                if (ampm=='AM'):
                    firstSlot += 1
                else:
                    fifthSlot += 1
            elif ((hour >= 3 and hour < 6) or (hour == 6 and minute == 0)):
                if(ampm=='AM'):
                    secondSlot += 1
                else:
                    sixthSlot += 1
            elif ((hour >= 6 and hour < 9) or (hour == 9 and minute == 0)):
                if(ampm=='AM'):
                    thirdSlot += 1
                else:
                    seventhSlot += 1
            elif ((hour >= 9 and hour < 12) or (hour == 12 and minute == 0)):
                if(ampm=='AM' and hour!=12):
                    fourthSlot += 1
                else:
                    eigthSlot += 1

        mostDengerousStreets=sorted(streets, key=streets.get, reverse=True)[:3] #sorting the dictionay streets and retrievind the top 3 streets with the highest no of crimes

        #A dictionay to store the final crime report
        finalReport = {"total_crime": totalCrime,
                       "the_most_dangerous_streets": mostDengerousStreets,
                       "crime_type_count": crimeType,
                       "event_time_count": {
                           "12:01am-3am": firstSlot,
                           "3:01am-6am": secondSlot,
                           "6:01am-9am": thirdSlot,
                           "9:01am-12noon": fourthSlot,
                           "12:01pm-3pm": fifthSlot,
                           "3:01pm-6pm": sixthSlot,
                           "6:01pm-9pm": seventhSlot,
                           "9:01pm-12midnight": eigthSlot
                       }}

        yield finalReport #displaying the final report

application = Application([CrimeReportService],
    tns='spyne.check.crime',
    in_protocol=HttpRpc(validator='soft'),
    out_protocol=JsonDocument())

if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    wsgi_app = WsgiApplication(application)
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()
