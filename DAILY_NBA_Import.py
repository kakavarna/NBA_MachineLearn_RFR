######################################################################
#IMPORTS

import requests
import json
import utilFunctions
from utilFunctions import convertStr
import datetime


######################################################################
#GLOBAL VARIABLES

config_data = utilFunctions.read_APIconfig()
payload={}
headers = {
    'x-rapidapi-key': config_data['api_key'],
    'x-rapidapi-host': config_data['api_host']
}

errorLogPath = "C:\\Users\\vinay\\Documents\\dataImportErrors.txt"

######################################################################
#FUNCTIONS
    
#FUNCTION getGameStats - retrieves game stats based on given game ID
def getGameStats(headers, baseurl, game):
    url = baseurl + "games/statistics"
    params = {
        'id': game['id']
    }
    response = requests.get(url, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data['response']
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

#FUNCTION saveGameData - takes game data and statisctic to store in sql server
def saveGameData(game, team):
    home = 0
    curTeamID = team['team']['id']
    homeTeamID = game['teams']['home']['id']
    teamStats = team['statistics'][0]
    gameScores = None
    gameDate = utilFunctions.getDateFromString(game['date']['start'])

    if(curTeamID == homeTeamID):
        home = 1
        gameScores = game['scores']['home']
    else:
        gameScores = game['scores']['visitors']
    insertSQL = '''INSERT INTO tbl_games (game_id,league,season,
    date,teamName,teamCode,home,points,q1score,q2score,q3score,
    q4score,plusminus,fastBreakPoints,pointsInPaint,biggestLead,
    secondChancePoints,pointsOffTurnOvers,LongestRun,fgm,fga,fgp,
    ftm,fta,ftp,tpm,tpa,tpp,offReb,defReb,totReb,assists,pFouls,
    steals,turnovers,blocks) VALUES ('''
    insertSQL += str(game['id']) + ","
    insertSQL += "'" + game['league'] + "',"
    insertSQL += str(game['season']) + ","
    insertSQL += "'" + str(gameDate) + "',"
    insertSQL += "'" + team['team']['name'] + "',"
    insertSQL += "'" + team['team']['code'] + "',"
    insertSQL += convertStr(home) + ","
    insertSQL += convertStr(gameScores['points']) + ","
    try:
        q1Score = convertStr(gameScores['linescore'][0])
        q2Score = convertStr(gameScores['linescore'][1])
        q3Score = convertStr(gameScores['linescore'][2])
        q4Score = convertStr(gameScores['linescore'][3])
        insertSQL += q1Score + ","
        insertSQL += q2Score + ","
        insertSQL += q3Score + ","
        insertSQL += q4Score + ","
    except:
        with open(errorLogPath, "a") as myfile:
            myfile.write("\nFaulty LineScore for GameID:\n" + str(game['id']))
    insertSQL += convertStr(teamStats['plusMinus']) + ","
    insertSQL += convertStr(teamStats['fastBreakPoints']) + ","
    insertSQL += convertStr(teamStats['pointsInPaint']) + ","
    insertSQL += convertStr(teamStats['biggestLead']) + ","
    insertSQL += convertStr(teamStats['secondChancePoints']) + ","
    insertSQL += convertStr(teamStats['pointsOffTurnovers']) + ","
    insertSQL += convertStr(teamStats['longestRun']) + ","
    insertSQL += convertStr(teamStats['fgm']) + ","
    insertSQL += convertStr(teamStats['fga']) + ","
    insertSQL += convertStr(teamStats['fgp']) + ","
    insertSQL += convertStr(teamStats['ftm']) + ","
    insertSQL += convertStr(teamStats['fta']) + ","
    insertSQL += convertStr(teamStats['ftp']) + ","
    insertSQL += convertStr(teamStats['tpm']) + ","
    insertSQL += convertStr(teamStats['tpa']) + ","
    insertSQL += convertStr(teamStats['tpa']) + ","
    insertSQL += convertStr(teamStats['offReb']) + ","
    insertSQL += convertStr(teamStats['defReb']) + ","
    insertSQL += convertStr(teamStats['totReb']) + ","
    insertSQL += convertStr(teamStats['assists']) + ","
    insertSQL += convertStr(teamStats['pFouls']) + ","
    insertSQL += convertStr(teamStats['steals']) + ","
    insertSQL += convertStr(teamStats['turnovers']) + ","
    insertSQL += convertStr(teamStats['blocks']) + ");"
    try:
        utilFunctions.executeNonQuery(insertSQL)
    except:
        with open(errorLogPath, "a") as myfile:
            myfile.write("\nFaulty Insert:\n"+insertSQL)
    return None

#FUNCTION getLastDateCheck - checks sql table for last date api was checked for game data
def getLastDateCheck():
    selectSQL = "SELECT Date FROM tbl_dates WHERE NAME = 'LastDateCheck' LIMIT 1"
    try:
        result = utilFunctions.selectQuery(selectSQL)
        return result[0][0]
    except:
        with open(errorLogPath, "a") as myfile:
            myfile.write("\nFaulty Select:\n"+selectSQL)
    return None

#FUNCTION setLastDateCheck - updates last date check value
def setLastDateCheck(setDateString):
    updateSQL = "UPDATE  tbl_dates SET DATE = '" + setDateString + "' WHERE NAME = 'LastDateCheck'"
    try:
        utilFunctions.executeNonQuery(updateSQL)
    except:
        with open(errorLogPath, "a") as myfile:
            myfile.write("\nFaulty Update:\n"+updateSQL)
    return None

#FUNCTION getNbaGameDay - returns all games for a given date
def getNbaGameDay(headers, baseurl, datestring):
    url = baseurl + "games"
    params = {
        'date': datestring
    }
    response = requests.get(url, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data['response']
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

######################################################################
#MAIN

def main():
    lastDateChecked = getLastDateCheck()
    todaysDate = datetime.date.today()
    while lastDateChecked < todaysDate:
        lastDateChecked += datetime.timedelta(days=1)
        dailyGames = getNbaGameDay(headers, config_data['api_host'], utilFunctions.ConvertDateToString(lastDateChecked))
        for game in dailyGames:
            gameStats = getGameStats(headers, config_data['api_host'], game)
            for team in gameStats:
                saveGameData(game, team)
    setLastDateCheck(utilFunctions.ConvertDateToString(todaysDate))

######################################################################
#Execute

main()

######################################################################