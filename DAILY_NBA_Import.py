######################################################################
#IMPORTS

import requests
import json
import utilFunctions
from utilFunctions import convertStr
import datetime
import utilNBA_ML_RFR
import pandas as pd
import pytz
from dateutil import parser
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

#FUNCTION getNbaGameDay - returns all games for a given date
def getNbaGameDayEastern(headers, baseurl, date):
    datestring = utilFunctions.ConvertDateToString(date)
    url = baseurl + "games"
    data = None
    games = []
    params = { 'date': datestring }
    response = requests.get(url, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()['response']
        #keep data if its a game for today in eastern time
        for game in data:
            gameTime = game.get('date').get('start')
            gameDate = convert_iso8601_to_eastern(gameTime).date()
            if(gameDate == date):
                games.append(game)
    else:
        print(f"Failed to retrieve data: {response.status_code}")
    #Check for the next eastern date
    nextdate = date + datetime.timedelta(days=1)
    nextdatestring = utilFunctions.ConvertDateToString(nextdate)
    params = { 'date': nextdatestring }
    response = requests.get(url, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()['response']
        #keep data if its a game for today in eastern time
        for game in data:
            gameTime = game.get('date').get('start')
            gameDate = convert_iso8601_to_eastern(gameTime).date()
            if(gameDate == date):
                games.append(game)
    else:
        print(f"Failed to retrieve data: {response.status_code}")
    return games

#FUNCTION getPlayerStats - retrieves player stats based on given game ID
def getPlayerStats(headers, baseurl, gameid, season):
    url = baseurl + "players/statistics"
    params = {
        'game': gameid,
        'season': season
    }
    response = requests.get(url, headers=headers, params=params)
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data['response']
    else:
        print(f"Failed to retrieve data: {response.status_code}")
        return None

#FUNCTION importNBAGameData - updates nba player data
def importNBAPlayerData():
    SelectSQL = "SELECT DISTINCT game_id, season FROM tbl_games WHERE PlayerImported = 0"
    gamesToTrack = utilFunctions.selectQuery(SelectSQL)
    for game in gamesToTrack:
        gameID = game[0]
        season = game[1]
        playerData = getPlayerStats(headers,config_data['api_host'],gameID,season)
        for player in playerData:
            savePlayerData(player,season)
        updateSQL = "UPDATE tbl_games SET PlayerImported = 1 WHERE game_id = "+ convertStr(gameID)
        utilFunctions.executeNonQuery(updateSQL)
    None

#FUNCTION importNBAGameData - updates nba game data
def importNBAGameData():
    lastDateChecked = getLastDateCheck()
    todaysDate = datetime.date.today()
    while lastDateChecked < (todaysDate):
        dailyGames = getNbaGameDayEastern(headers, config_data['api_host'], lastDateChecked)
        i = 0
        for game in dailyGames:
            status = game.get("status").get("long")
            if(status == "Finished"):
                gameStats = getGameStats(headers, config_data['api_host'], game)
                for team in gameStats:
                    saveGameData(game, team)
        lastDateChecked += datetime.timedelta(days=1)
    if(getLastDateCheck() < todaysDate): 
        setLastDateCheck(utilFunctions.ConvertDateToString(todaysDate-datetime.timedelta(days=1)))

#FUNCTION getRollingAverages - gets rolling averages from sql view
def getRollingAverages(teamCode,Home):
    SelectSQL = "SELECT AvgTotReb,AvgFGM,AvgFGA,AvgFGP,AvgTPM,AvgTPA,AvgTPP,AvgFTM,AvgFTA,AvgFTP,AvgAssists FROM view_teamrollingaverages WHERE teamCode = '" + utilFunctions.convertStr(teamCode) + "'"
    averagedata =  utilFunctions.selectQuery(SelectSQL)
    averagesDict = {
        'AvgTotReb': averagedata[0][0],
        'AvgFGM': averagedata[0][1],
        'AvgFGA': averagedata[0][2],
        'AvgFGP': averagedata[0][3],
        'AvgTPM': averagedata[0][4],
        'AvgTPA': averagedata[0][5],
        'AvgTPP': averagedata[0][6],
        'AvgFTM': averagedata[0][7],
        'AvgFTA': averagedata[0][8],
        'AvgFTP': averagedata[0][9],
        'AvgAssists': averagedata[0][10]
    }
    averagesDict = {k:[v] for k,v in averagesDict.items()}
    averagesDF = pd.DataFrame(averagesDict)
    if(Home):
        averagesDF = averagesDF.rename(columns=lambda col: "home"+col)
    else:
        averagesDF = averagesDF.rename(columns=lambda col: "visitor"+col)
    return averagesDF

#FUNCTION predictTodaysGames - makes and stores predictions for games on todays eastern based date
def predictTodaysGames():
    model, featureEncoder, featureData, predictColumns = utilNBA_ML_RFR.getModelAndColumns()
    today = datetime.date.today()
    MLodds = getMoneylineOdds(utilFunctions.ConvertDateToString(today))
    todaysGames = getNbaGameDayEastern(headers, config_data['api_host'], today)
    for game in todaysGames:
        if(game.get("status").get("long") == "Scheduled"):
            game_id = game.get("id")
            home_team = game.get("teams").get("home").get("code")
            visitor_team = game.get("teams").get("visitors").get("code")
            homeName = game.get("teams").get("home").get("name")
            visitorName = game.get("teams").get("visitors").get("name")
            input_data = pd.DataFrame({
                'homeCode': [home_team],
                'visitorCode': [visitor_team],
                'Year': [today.year],
                'Month': [today.month],
                'Day': [today.day]
            })
            #get the averages to use in input
            homeAveragesData = getRollingAverages(home_team, 1)
            visitorAveragesData = getRollingAverages(visitor_team, 0)
            #Encode non-numerical data
            input_encoded = featureEncoder.transform(input_data[['homeCode', 'visitorCode']])
            input_encoded_df = pd.DataFrame(input_encoded, columns=featureEncoder.get_feature_names_out(['homeCode', 'visitorCode']))
            input_full = pd.concat([input_data[['Year', 'Month', 'Day']], input_encoded_df,homeAveragesData,visitorAveragesData], axis=1)
            input_full = input_full[featureData.columns]
            #predict
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
            for odds in MLodds:
                if(odds['home'] == homeName and odds['away'] == visitorName):
                    predictionDict.update(odds)
                    break
            savePrediction(predictionDict)

#FUNCTION saveGameData - takes game data and statisctics to store in sql server
def saveGameData(game, team):
    home = 0
    curTeamID = team['team']['id']
    homeTeamID = game['teams']['home']['id']
    teamStats = team['statistics'][0]
    gameScores = None
    gameDate = utilFunctions.getDateFromString(game['date']['start'])

    selectSQL = "SELECT * FROM tbl_games WHERE game_id = " + str(game['id']) + " AND teamCode = '" + team['team']['code'] + "'"
    result = utilFunctions.selectQuery(selectSQL)
    if(len(result)==0):
        if(curTeamID == homeTeamID):
            home = 1
            gameScores = game['scores']['home']
        else:
            gameScores = game['scores']['visitors']
        insertSQL = '''INSERT INTO tbl_games (game_id,league,season,
        date,teamName,teamCode,home,points,q1score,q2score,q3score,
        q4score,plusminus,fgm,fga,fgp,
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
        except Exception as e:
            print(e)
            with open(errorLogPath, "a") as myfile:
                myfile.write("\nFaulty LineScore for GameID:\n" + str(game['id']))
        insertSQL += convertStr(teamStats['plusMinus']) + ","
        insertSQL += convertStr(teamStats['fgm']) + ","
        insertSQL += convertStr(teamStats['fga']) + ","
        insertSQL += convertStr(teamStats['fgp']) + ","
        insertSQL += convertStr(teamStats['ftm']) + ","
        insertSQL += convertStr(teamStats['fta']) + ","
        insertSQL += convertStr(teamStats['ftp']) + ","
        insertSQL += convertStr(teamStats['tpm']) + ","
        insertSQL += convertStr(teamStats['tpa']) + ","
        insertSQL += convertStr(teamStats['tpp']) + ","
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
        except Exception as e:
            print(e)
            with open(errorLogPath, "a") as myfile:
                myfile.write("\nFaulty Insert:\n"+insertSQL)
    return None

#FUNCTION savePlayerData - takes player data and statisctics to store in sql server
def savePlayerData(playerGameStats,season):
    InsertSQL = "INSERT INTO tbl_playerstats"
    InsertSQL += "(player_id, game_id, season, firstName, lastName, teamName, teamCode, minutes, points, fgm, fga, fgp, ftm, fta, ftp, tpm, tpa, tpp, totReb, assists, steals, blocks) VALUES ("
    InsertSQL += convertStr(playerGameStats['player']['id']) + ","
    InsertSQL += convertStr(playerGameStats['game']['id']) + ","
    InsertSQL += convertStr(season) + ","
    InsertSQL += "'" + playerGameStats['player']['firstname'].replace("'","''")  + "',"
    InsertSQL += "'" + playerGameStats['player']['lastname'].replace("'","''") + "',"
    InsertSQL += "'" + playerGameStats['team']['name'] + "',"
    InsertSQL += "'" + playerGameStats['team']['code'] + "',"
    InsertSQL += convertStr(playerGameStats['min']) + ","
    InsertSQL += convertStr(playerGameStats['points']) + ","
    InsertSQL += convertStr(playerGameStats['fgm']) + ","
    InsertSQL += convertStr(playerGameStats['fga']) + ","
    InsertSQL += convertStr(playerGameStats['fgp']) + ","
    InsertSQL += convertStr(playerGameStats['ftm']) + ","
    InsertSQL += convertStr(playerGameStats['fta']) + ","
    InsertSQL += convertStr(playerGameStats['ftp']) + ","
    InsertSQL += convertStr(playerGameStats['tpm']) + ","
    InsertSQL += convertStr(playerGameStats['tpa']) + ","
    InsertSQL += convertStr(playerGameStats['tpp']) + ","
    InsertSQL += convertStr(playerGameStats['totReb']) + ","
    InsertSQL += convertStr(playerGameStats['assists']) + ","
    InsertSQL += convertStr(playerGameStats['steals']) + ","
    InsertSQL += convertStr(playerGameStats['blocks'])
    InsertSQL += ")"
    try:
        utilFunctions.executeNonQuery(InsertSQL)
    except:
        with open(errorLogPath, "a") as myfile:
            myfile.write("\nFaulty Insert:\n"+InsertSQL)

#FUNCTION savePrediction - saves row to sql table if prediction record does not exist           
def savePrediction(predictionDict):
    selectSQL = "SELECT * FROM tbl_predictions WHERE game_id = " + convertStr(predictionDict.get("game_id"))
    result = utilFunctions.selectQuery(selectSQL)
    if(len(result)==0):
        insertSQL = "INSERT INTO tbl_predictions(game_id,date,homeCode,visitorCode,homePoints,visitorPoints,totalPoints,homePlusMinus,visitorPlusMinus,homeMLodds,visitorMLodds) VALUES("
        insertSQL += convertStr(predictionDict.get("game_id")) + ","
        insertSQL += "'" + predictionDict.get("date") + "',"
        insertSQL += "'" + predictionDict.get("homeCode") + "',"
        insertSQL += "'" + predictionDict.get("visitorCode") + "',"
        insertSQL += convertStr(predictionDict.get("homePoints")) + ","
        insertSQL += convertStr(predictionDict.get("visitorPoints")) + ","
        insertSQL += convertStr(predictionDict.get("totalPoints")) + ","
        insertSQL += convertStr(predictionDict.get("homeplusminus")) + ","
        insertSQL += convertStr(predictionDict.get("visitorplusminus")) + ","
        insertSQL += convertStr(predictionDict.get('home_h2h_odds')) + ","
        insertSQL += convertStr(predictionDict.get('away_h2h_odds')) + ");"
        try:
            utilFunctions.executeNonQuery(insertSQL)
        except:
            with open(errorLogPath, "a") as myfile:
                myfile.write("\nFaulty Insert:\n"+insertSQL)
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

#FUNCTION convert_iso8601_to_eastern - converts iso time string to easter datetime object
def convert_iso8601_to_eastern(iso8601_time):
    # Parse the ISO 8601 time string using dateutil.parser
    utc_time = parser.isoparse(iso8601_time)
    # Define the UTC and Eastern timezone
    utc_zone = pytz.utc
    eastern_zone = pytz.timezone("America/New_York")
    # Localize the time to UTC
    utc_time = utc_time.replace(tzinfo=utc_zone)
    # Convert to Eastern Time
    eastern_time = utc_time.astimezone(eastern_zone)
    return eastern_time

#FUNCTION printDict - outputs a dict object in readable formate
def printDict(dict):
    print("\n")
    for key, value in dict.items():
        print(f"{key}: {value}")
        
def predictMatchup(visitor,home,year,month,day):
    model, featureEncoder, featureData, predictColumns = utilNBA_ML_RFR.getModelAndColumns()
    home_team = home
    visitor_team = visitor
    input_data = pd.DataFrame({
        'homeCode': [home_team],
        'visitorCode': [visitor_team],
        'Year': year,
        'Month': month,
        'Day': day
     })
    #get the averages to use in input
    homeAveragesData = getRollingAverages(home_team, 1)
    visitorAveragesData = getRollingAverages(visitor_team, 0)
    #Encode non-numerical data
    input_encoded = featureEncoder.transform(input_data[['homeCode', 'visitorCode']])
    input_encoded_df = pd.DataFrame(input_encoded, columns=featureEncoder.get_feature_names_out(['homeCode', 'visitorCode']))
    input_full = pd.concat([input_data[['Year', 'Month', 'Day']], input_encoded_df,homeAveragesData,visitorAveragesData], axis=1)
    input_full = input_full[featureData.columns]
    #predict and save
    prediction = model.predict(input_full)
    predictTable = [predictColumns,prediction]
    wantedColumns = ['homePoints','homeplusminus','visitorPoints','visitorplusminus','totalPoints']
    predictionDict = {
        'homeCode': home_team,
        'visitorCode': visitor_team
    }
    i = 0
    while i < len(wantedColumns):
        predictionDict.update({wantedColumns[i]:prediction[0,predictColumns.index(wantedColumns[i])]})
        i += 1
    printDict(predictionDict)
    
def getMoneylineOdds(today):
    host = config_data['odds_api_host']
    key = config_data['odds_api_key']
    requestUrl = host + "/v4/sports/basketball_nba/odds/?apiKey=" + key + "&regions=us&markets=h2h"
    response = requests.get(requestUrl)
    if response.status_code == 200:
        data = response.json()
        odds_list = []
        for event in data:
            gameDate = utilFunctions.ConvertDateToString(convert_iso8601_to_eastern(event['commence_time']).date())
            if (gameDate == today):
                home_team = event["home_team"]
                away_team = event["away_team"]
                fanduel_odds = next(
                    (book for book in event["bookmakers"] if book["title"] == "FanDuel"), None
                )
                if fanduel_odds:
                    h2h_odds = fanduel_odds["markets"][0]["outcomes"]  # Assuming first market is h2h
                    home_odds = next((odd["price"] for odd in h2h_odds if odd["name"] == home_team), None)
                    away_odds = next((odd["price"] for odd in h2h_odds if odd["name"] == away_team), None)
                    odds_list.append({
                        "home": home_team,
                        "away": away_team,
                        "home_h2h_odds": home_odds,
                        "away_h2h_odds": away_odds
                    })
        return odds_list
    else:
        print(f"Error: {response.status_code}, {response.text}")
        return []

######################################################################
#MAIN

def main():
    print("--Recording Completed Games--")
    importNBAGameData()
    print("--Making Predictions--")
    predictTodaysGames()
    print("--Getting Player Data--")
    importNBAPlayerData()
    print("DONE!!!!")

######################################################################
#Execute

main()

######################################################################