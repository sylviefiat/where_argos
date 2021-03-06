import http.client
import re
import csv
import math
import datetime
import smtplib
import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen, PIPE
import xml.dom.minidom
import xml.etree.ElementTree as ET

#http://ws-argos.cls.fr/argosDws/services/DixService?wsdl
ARGOS_HOST = "ws-argos.cls.fr"

def argosRequest(request):
    conn = http.client.HTTPConnection(ARGOS_HOST)
    conn.request("POST", "/argosDws/services/DixService", request)
    response = conn.getresponse()
    #print response.status, response.reason, response.msg
    data = response.read()
    print(data)
    conn.close()
    return data

def cleanupXml(data):
    body = re.search("<return>(.*)</return>", data, flags=re.S)
    if (body):
        body = body.group(1)
        body = re.sub("&lt;", "<", body)
        body = re.sub("&gt;", ">", body)
        body = re.sub("&amp;", "&", body)
        body = re.sub("&lt;", "<", body)
        ugly_xml = xml.dom.minidom.parseString(body)
        ugly_xml = ugly_xml.toprettyxml(indent='  ')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)    
        pretty_xml = text_re.sub('>\g<1></', ugly_xml)
        return pretty_xml

def cleanupCsv(data):
    body = re.search("<return>(.*)</return>", data, flags=re.S)
    if (body):
        body = body.group(1)
        return body


def getPlatforms(username, password, programNumber):
    argosXml = getXml(username, password, programNumber, type="program", nbPassByPtt=1)
    root = ET.fromstring(argosXml)
    platformIds = []
    for platform in root.findall(".//platform"):
        #ET.dump(platform)
        platformIds.append(int(platform.find("platformId").text))
    return platformIds



def getCsv(username, password, id, type="platform", nbPassByPtt=10, nbDaysFromNow=10, mostRecentPassages="true", displaySensor="false"):
    if (type == "program"):
        type = "<typ:programNumber>" + str(id) + "</typ:programNumber>"
    else:
        type = "<typ:platformId>" + str(id) + "</typ:platformId>"

    request = (
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:typ="http://service.dataxmldistribution.argos.cls.fr/types">\n'
        '<soap:Header/>\n'
        '<soap:Body>\n'
        '<typ:csvRequest>\n'
        '<typ:username>%s</typ:username>\n'
        '<typ:password>%s</typ:password>\n'
        '%s\n'
        '<typ:nbPassByPtt>%d</typ:nbPassByPtt>\n'
        '<typ:nbDaysFromNow>%d</typ:nbDaysFromNow>\n'
        '<typ:mostRecentPassages>%s</typ:mostRecentPassages>\n'
        '<typ:displayLocation>true</typ:displayLocation>\n'
        '<typ:displayRawData>false</typ:displayRawData>\n'
        '<typ:displaySensor>%s</typ:displaySensor>\n'
        '<typ:showHeader>true</typ:showHeader>\n'
        '</typ:csvRequest>\n'
        '</soap:Body>\n'
        '</soap:Envelope>'
        ) % (username, password, type, nbPassByPtt, nbDaysFromNow, mostRecentPassages, displaySensor)


    #print request
    data = argosRequest(request)
    data = cleanupCsv(data)
    return data


def getKml(username, password, id, type="platform", nbPassByPtt=10, nbDaysFromNow=10, mostRecentPassages="true"):
    if (type == "program"):
        type = "<typ:programNumber>" + str(id) + "</typ:programNumber>"
    else:
        type = "<typ:platformId>" + str(id) + "</typ:platformId>"

    request = (
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:typ="http://service.dataxmldistribution.argos.cls.fr/types">\n'
        '<soap:Header/>\n'
        '<soap:Body>\n'
        '<typ:kmlRequest>\n'
        '<typ:username>%s</typ:username>\n'
        '<typ:password>%s</typ:password>\n'
        '%s\n'
        '<typ:nbPassByPtt>%d</typ:nbPassByPtt>\n'
        '<typ:nbDaysFromNow>%d</typ:nbDaysFromNow>\n'
        '<typ:mostRecentPassages>%s</typ:mostRecentPassages>\n'
        '<typ:displayDescription>true</typ:displayDescription>\n'
        '</typ:kmlRequest>\n'
        '</soap:Body>\n'
        '</soap:Envelope>'
        ) % (username, password, type, nbPassByPtt, nbDaysFromNow, mostRecentPassages)


    #print request
    data = argosRequest(request)
    data = cleanupXml(data)
    return data


def getXml(username, password, id, type="platform", nbPassByPtt=10, nbDaysFromNow=10, mostRecentPassages="true", displaySensor="false"):
    if (type == "program"):
        type = "<typ:programNumber>" + str(id) + "</typ:programNumber>"
    else:
        type = "<typ:platformId>" + str(id) + "</typ:platformId>"

    request = (
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:typ="http://service.dataxmldistribution.argos.cls.fr/types">\n'
        '<soap:Header/>\n'
        '<soap:Body>\n'
        '<typ:xmlRequest>\n'
        '<typ:username>%s</typ:username>\n'
        '<typ:password>%s</typ:password>\n'
        '%s\n'
        '<typ:nbPassByPtt>%d</typ:nbPassByPtt>\n'
        '<typ:nbDaysFromNow>%d</typ:nbDaysFromNow>\n'
        '<typ:mostRecentPassages>%s</typ:mostRecentPassages>\n'
        '<typ:displayLocation>true</typ:displayLocation>\n'
        '<typ:displayRawData>false</typ:displayRawData>\n'
        '<typ:displaySensor>%s</typ:displaySensor>\n'
        '</typ:xmlRequest>\n'
        '</soap:Body>\n'
        '</soap:Envelope>'
        ) % (username, password, type, nbPassByPtt, nbDaysFromNow, mostRecentPassages, displaySensor)


    #print request
    data = argosRequest(request)
    data = cleanupXml(data)
    return data

def getXsd():
    request = (
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:typ="http://service.dataxmldistribution.argos.cls.fr/types">\n'
        '<soap:Header/>\n'
        '<soap:Body>\n'
        '<typ:xsdRequest/>\n'
        '</soap:Body>\n'
        '</soap:Envelope>'
        ) % ()


    #print request
    data = argosRequest(request)
    data = cleanupXml(data)
    return data


def getLocations(argos_xml):
    root = ET.fromstring(argos_xml)
    locations = []
    for location in root.findall(".//location"):
        #ET.dump(location)
        location_date = location.find("locationDate").text
        latitude = float(location.find("latitude").text)
        longitude = float(location.find("longitude").text)
        current_location = [location_date, latitude, longitude]
        locations.append(current_location)

    if (len(locations) == 0):
        return None
    else:
        return locations



def get_current_location(username, password, platform_id):
    argos_xml = getXml(username, password, platform_id)
    locations = getLocations(argos_xml)
    current_loc = sorted(locations).pop()
    return current_loc

def calcul_speed(latitude1,longitude1, date1, latitude2, longitude2, date2):
    lon1=float(longitude1.replace(',','.'))
    lon2=float(longitude2.replace(',','.'))
    lat1=float(latitude1.replace(',','.'))
    lat2=float(latitude2.replace(',','.')) 
    d1=datetime.datetime.strptime(date1, '%Y/%m/%d %H:%M:%S')
    d2=datetime.datetime.strptime(date2, '%Y/%m/%d %H:%M:%S')
    distance = math.acos(math.sin(math.radians(lon1))*math.sin(math.radians(lon2))+math.cos(math.radians(lon1))*math.cos(math.radians(lon2))*math.cos(math.radians(lat1-lat2)))*6371
    elapsedTime = d2 - d1 
    temps = elapsedTime.days * 24 + elapsedTime.seconds / 3600.0
    vitesse = 0 if temps==0 else distance / temps
    return distance,temps,vitesse


def convertCSV_for_DTSI(file):    
    with open(file, 'r', encoding="utf8") as f:        
        fieldnames = ['N° ID','Date de loc.','Latitude (degré décimal)','Longitude  (degré décimal)','Chronologie'] 
        filename= "argos_where_"+datetime.datetime.today().strftime('%Y-%m-%d')+".csv"
        writer = csv.DictWriter(open("./exemples/"+filename, 'w'), fieldnames=fieldnames,delimiter=';')
        writer.writeheader()

        reader = csv.DictReader(f,delimiter=';')
        nid = 0        
        for row in reader:          
            if(row[fieldnames[0]]!=nid):
                latitude1 = 0
                longitude1 = 0
                date1 = 0        
                n = 1
                nid=row[fieldnames[0]]
            elif not((latitude1==row[fieldnames[3]] and longitude1==row[fieldnames[2]] and date1==row[fieldnames[1]]) or row[fieldnames[1]]==''):                
                if (latitude1==0 and longitude1==0 and date1==0):
                    distance,temps,vitesse=0,0,0
                else:
                    distance,temps,vitesse=calcul_speed(latitude1,longitude1, date1, row[fieldnames[3]], row[fieldnames[2]], row[fieldnames[1]])
                if(vitesse<12):
                    writer.writerow({fieldnames[0]: row[fieldnames[0]], fieldnames[1]: row[fieldnames[1]], fieldnames[2]: row[fieldnames[2]], fieldnames[3]: row[fieldnames[3]],fieldnames[4]: n})
                    nid1=row[fieldnames[0]]
                    latitude1=row[fieldnames[3]]
                    longitude1=row[fieldnames[2]]
                    date1=row[fieldnames[1]]
                    n = n+1
    return "./exemples/"+filename

def sendcsv_mail_with_google(expediteur,destinataire,file,username,password):
    emailfrom = expediteur
    emailto = destinataire
    fileToSend = file
    username = "user"
    password = "password"

    msg = MIMEMultipart()
    msg["From"] = emailfrom
    msg["To"] = emailto
    msg["Subject"] = "New argos data"
    msg.preamble = "Please find attached new argos data for WHERE project"

    ctype, encoding = mimetypes.guess_type(fileToSend)
    if ctype is None or encoding is not None:
        ctype = "application/octet-stream"

    maintype, subtype = ctype.split("/", 1)

    if maintype == "text":
        fp = open(fileToSend)
        # Note: we should handle calculating the charset
        attachment = MIMEText(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == "image":
        fp = open(fileToSend, "rb")
        attachment = MIMEImage(fp.read(), _subtype=subtype)
        fp.close()
    elif maintype == "audio":
        fp = open(fileToSend, "rb")
        attachment = MIMEAudio(fp.read(), _subtype=subtype)
        fp.close()
    else:
        fp = open(fileToSend, "rb")
        attachment = MIMEBase(maintype, subtype)
        attachment.set_payload(fp.read())
        fp.close()
        encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=fileToSend)
    msg.attach(attachment)

    server = smtplib.SMTP("smtp.gmail.com:587")
    server.starttls()
    server.login(username,password)
    server.sendmail(emailfrom, emailto, msg.as_string())
    server.quit()

def sendcsv_mail_with_sendmail(expediteur,destinataire,fileToSend):
    html = MIMEText("<html><head><title>New argos data</title></head><body>Please find attached new argos data for WHERE project</body>", "html")
    msg = MIMEMultipart("alternative")
    

    msg["From"] = expediteur
    msg["To"] = destinataire
    msg["Subject"] = "New argos data"
    msg.add_header('Content-Disposition', 'attachment', filename=('utf8', '', fileToSend))

    msg.attach(html)

    p = Popen(["/usr/sbin/sendmail", "-t"], stdin=PIPE)
    p.communicate(msg.as_bytes())


if __name__ == '__main__':
    #argos_csv=getCsv('GARRIGUE','BOSSE_2016',IDPROGRAM,'program',10, 20, "true", "false")
    argos_csv='./exemples/ArgosData_2016_09_23-25.csv'
    file = convertCSV_for_DTSI(argos_csv)
    #sendcsv_mail_with_google("devtest.ird@gmail.com","sylvie.fiat@ird.fr",file,"devtest.ird@gmail.com","DEV2016test")
    sendcsv_mail_with_sendmail("sylvie.fiat@ird.fr","sylvie.fiat@ird.fr",file)

    