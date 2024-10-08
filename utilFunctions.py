import configparser
import mysql
import mysql.connector
from dateutil import parser



def read_DBconfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    db_user = config.get('Database', 'db_user')
    db_host = config.get('Database', 'db_host')
    db_pass = config.get('Database', 'db_pass')
    db_name = config.get('Database', 'db_name')
    config_values = {
        'db_user': db_user,
        'db_host': db_host,
        'db_pass': db_pass,
        'db_name': db_name
    }
    return config_values

def read_APIconfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    api_key = config.get('API', 'api_key')
    api_host = config.get('API', 'api_host')
    api_values = {
        'api_key': api_key,
        'api_host': api_host
    }
    return api_values

def getDBConnection():
    config_data = read_DBconfig()
    cnx = mysql.connector.connect(user=config_data['db_user'], 
                              password=config_data['db_pass'],
                              host=config_data['db_host'],
                              database=config_data['db_name'])
    return cnx

def selectQuery(query):
    cnx = getDBConnection()
    cursor = cnx.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    cnx.close()
    return result

def executeNonQuery(query):
    cnx = getDBConnection()
    cursor = cnx.cursor()
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()

def getDateFromString(rawdate):
    yourdate = parser.parse(rawdate).strftime("%Y-%m-%d")
    return yourdate

def ConvertStringToDate(dateString):
    yourdate = parser.parse(dateString)
    return yourdate

def ConvertDateToString(stringDate):
    yourString = stringDate.strftime("%Y-%m-%d")
    return yourString

def convertStr(data):
    if(data == None):
        data = 0
    return str(data)
