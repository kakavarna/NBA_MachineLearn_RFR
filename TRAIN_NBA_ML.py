######################################################################
#IMPORTS

from sklearn.model_selection import train_test_split
import utilFunctions
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from numpy import array
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score

######################################################################
#GLOBAL VARIABLES

######################################################################
#FUNCTIONS

######################################################################
#MAIN

def main():
    # Load your data (replace with the actual loading code)
    # Assuming you have a function to get the SQL data, else read from CSV
    cnx = utilFunctions.getDBConnection()
    data = pd.read_sql_query('SELECT * FROM view_train', cnx)
    cnx.close()

    # Preprocessing
    # Convert 'Date' column (YYYY-mm-dd) to individual features: year, month, day
    data['Year'] = data['date'].apply(lambda x: x.year)
    data['Month'] = data['date'].apply(lambda x: x.month)
    data['Day'] = data['date'].apply(lambda x: x.day)
    data = data.drop('date', axis=1)

    # One-hot encode categorical feature columns and create dataframe
    categorical_colsFEATURE = ['homeCode', 'visitorCode']
    encoderFEATURE = OneHotEncoder(sparse_output=False)
    encoded_Fcols = encoderFEATURE.fit_transform(data[categorical_colsFEATURE])
    encoded_Featureframe = pd.DataFrame(encoded_Fcols, columns=encoderFEATURE.get_feature_names_out(categorical_colsFEATURE))
    
    # One-hot encode categorical target columns and create dataframe
    categorical_colsTARGET = ['HalfTimeWinner', 'FullTimeWinner']
    encoderTARGET = OneHotEncoder(sparse_output=False)
    encoded_Tcols = encoderTARGET.fit_transform(data[categorical_colsTARGET])
    encoded_Targetframe = pd.DataFrame(encoded_Tcols, columns=encoderTARGET.get_feature_names_out(categorical_colsTARGET))
    
    # Drop original categorical columns and add encoded frames
    data = data.drop(categorical_colsFEATURE, axis=1)
    data = data.drop(categorical_colsTARGET, axis=1)
    data = pd.concat([data,encoded_Featureframe],axis=1)
    data = pd.concat([data,encoded_Targetframe],axis=1)

    # Define feature columns and assign feature data to X
    feature_cols = ['Year', 'Month', 'Day'] + [col for col in encoded_Featureframe.columns]
    X = data[feature_cols]

    # Define target columns and assign target data to y
    #target_cols = [col for col in encoded_df.columns if 'HalfTimeWinner' in col or 'FullTimeWinner' in col]
    target_cols = [col for col in data.columns if col not in encoded_Featureframe.columns]
    y = data[target_cols]

    # Split data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Initialize and train the model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Make predictions and evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f'Mean Squared Error: {mse}')
    
    # Get user input for home team and visitor team
    home_team = 'LAC'
    visitor_team = 'BKN'

    # Create a new DataFrame for the user input
    input_data = pd.DataFrame({
        'homeCode': [home_team],
        'visitorCode': [visitor_team],
        'Year': [2024],   # Replace with the current or desired year
        'Month': [10],     # Replace with the current or desired month
        'Day': [8]       # Replace with the current or desired day
    })

    # Encode the input data (only homeCode and visitorCode)
    input_encoded = encoderFEATURE.transform(input_data[['homeCode', 'visitorCode']])
    input_encoded_df = pd.DataFrame(input_encoded, columns=encoderFEATURE.get_feature_names_out(['homeCode', 'visitorCode']))


    # Add date information to the input
    input_full = pd.concat([input_data[['Year', 'Month', 'Day']], input_encoded_df], axis=1)

    # Ensure all columns match between training data and input data
    # Missing columns like 'FullTimeWinner', 'HalfTimeWinner' need to be added
    missing_cols = set(X.columns) - set(input_full.columns)
    for col in missing_cols:
        input_full[col] = 0

    # Reorder the columns to match the training data
    input_full = input_full[X.columns]

    # Make predictions
    prediction = model.predict(input_full)

    # Output the predicted result
    predictTable = [y.columns,prediction]
    indexCol = 0
    predictColumns = ['homePoints','homeplusminus','visitorPoints','visitorplusminus','totalPoints','HalfTimeWinner_'+home_team,'HalfTimeWinner_'+visitor_team,'FullTimeWinner_'+home_team,'FullTimeWinner_'+visitor_team]
    print("(home){} vs (visitor){}".format(home_team,visitor_team))
    while indexCol < y.columns.size:
        if(predictColumns.__contains__(y.columns[indexCol])):
            print("{} : {}".format(y.columns[indexCol], prediction[0,indexCol]))
        indexCol = indexCol + 1

main()

######################################################################
