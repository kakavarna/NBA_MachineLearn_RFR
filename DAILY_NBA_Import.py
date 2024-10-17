######################################################################
#IMPORTS

import requests
import json
import utilFunctions
from utilFunctions import convertStr
import datetime
import utilNBA_ML_RFR
import pandas as pd

######################################################################
#GLOBAL VARIABLES

config_data = utilFunctions.read_APIconfig()
payload={}
headers = {
    'x-rapidapi-key': config_data['api_key'],
    'x-rapidapi-host': config_data['api_host']
}

errorLogPath = "C:\\Users\\vinay\\Documents\\dataImportErrors.txt"
model = None

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

#FUNCTION importNBAGameData - updates nba game data
def importNBAGameData():
    lastDateChecked = getLastDateCheck()
    todaysDate = datetime.date.today()
    while lastDateChecked < todaysDate:
        lastDateChecked += datetime.timedelta(days=1)
        dailyGames = getNbaGameDay(headers, config_data['api_host'], utilFunctions.ConvertDateToString(lastDateChecked))
        for game in dailyGames:
            gameStats = getGameStats(headers, config_data['api_host'], game)
            for team in gameStats:
                saveGameData(game, team)
    if(getLastDateCheck() < todaysDate): 
        setLastDateCheck(utilFunctions.ConvertDateToString(todaysDate))

def predictTodaysGames():
    model, featureEncoder, featureData, predictColumns = utilNBA_ML_RFR.getModelAndColumns()
    today = datetime.date.today()
    todaysGames = getNbaGameDay(headers, config_data['api_host'], utilFunctions.ConvertDateToString(today))
    for game in todaysGames:
        game_id = game.get("id")
        home_team = game.get("teams").get("home").get("code")
        visitor_team = game.get("teams").get("visitors").get("code")
        input_data = pd.DataFrame({
            'homeCode': [home_team],
            'visitorCode': [visitor_team],
            'Year': [today.year],
            'Month': [today.month],
            'Day': [today.day]
        })
        input_encoded = featureEncoder.transform(input_data[['homeCode', 'visitorCode']])
        input_encoded_df = pd.DataFrame(input_encoded, columns=featureEncoder.get_feature_names_out(['homeCode', 'visitorCode']))
        input_full = pd.concat([input_data[['Year', 'Month', 'Day']], input_encoded_df], axis=1)
        input_full = input_full[featureData.columns]
        prediction = model.predict(input_full)
        predictTable = [predictColumns,prediction]
        wantedColumns = ['homePoints','homeplusminus','visitorPoints','visitorplusminus','totalPoints']
        predictionDict = {
            'game_id' : game_id,
            'date' : utilFunctions.ConvertDateToString(today),
            'homeCode': home_team,
            'visitorCode': visitor_team
        }
        i = 0
        while i < len(wantedColumns):
            predictionDict.update({wantedColumns[i]:prediction[0,predictColumns.index(wantedColumns[i])]})
            i += 1
        print("\n")
        printDict(predictionDict)
        savePrediction(predictionDict)
            
def savePrediction(predictionDict):
    selectSQL = "SELECT * FROM tbl_predictions WHERE game_id = " + convertStr(predictionDict.get("game_id"))
    result = utilFunctions.selectQuery(selectSQL)
    if(len(result)==0):
        insertSQL = "INSERT INTO tbl_predictions(game_id,date,homeCode,visitorCode,homePoints,visitorPoints,totalPoints,homePlusMinus,visitorPlusMinus) VALUES("
        insertSQL += convertStr(predictionDict.get("game_id")) + ","
        insertSQL += "'" + predictionDict.get("date") + "',"
        insertSQL += "'" + predictionDict.get("homeCode") + "',"
        insertSQL += "'" + predictionDict.get("visitorCode") + "',"
        insertSQL += convertStr(predictionDict.get("homePoints")) + ","
        insertSQL += convertStr(predictionDict.get("visitorPoints")) + ","
        insertSQL += convertStr(predictionDict.get("totalPoints")) + ","
        insertSQL += convertStr(predictionDict.get("homeplusminus")) + ","
        insertSQL += convertStr(predictionDict.get("visitorplusminus")) + ");"
        try:
            utilFunctions.executeNonQuery(insertSQL)
        except:
            with open(errorLogPath, "a") as myfile:
                myfile.write("\nFaulty Insert:\n"+insertSQL)
        return None

def printDict(dict):
    for key, value in dict.items():
        print(f"{key}: {value}")
        
######################################################################
#MAIN

def main():
    importNBAGameData()
    predictTodaysGames()

######################################################################
#Execute

main()

######################################################################