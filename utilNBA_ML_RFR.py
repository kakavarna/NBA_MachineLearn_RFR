######################################################################
#IMPORTS

from sklearn.model_selection import train_test_split
import utilFunctions
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

######################################################################
#GLOBAL VARIABLES

######################################################################
#FUNCTIONS
def getTrainingdata():
    cnx = utilFunctions.getDBConnection()
    data = pd.read_sql_query('SELECT * FROM view_train', cnx)
    cnx.close()
    return data

def getModelAndColumns():
    # Load your data (replace with the actual loading code)
    data = getTrainingdata()
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
    
    # Drop original categorical columns and add encoded frames
    data = data.drop(categorical_colsFEATURE, axis=1)
    data = pd.concat([data,encoded_Featureframe],axis=1)

    # Define feature columns and assign feature data to X
    feature_cols = ['Year', 'Month', 'Day'] + [col for col in encoded_Featureframe.columns]
    X = data[feature_cols]
    # Define target columns and assign target data to y
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
    return model, encoderFEATURE, X, target_cols

######################################################################
