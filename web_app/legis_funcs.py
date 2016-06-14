#legis_funcs.py
#This will contain all of the functions used by the legislatr web-app.
#Created By, Ethan D. Peck

import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from sklearn import linear_model
from sklearn.ensemble import RandomForestClassifier
import pickle

def runModel(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    result = model.predict(X)
    return result

def modelConf(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    P = model.predict_proba(X)
    Pr = max(P[0])*100. #convert to percent
    return Pr

def getBill(bill_type,bill_number,engine):
    bill = retrieveFeatures(bill_type,bill_number,engine)
    return bill 

def getResult(model,bill_type,bill_number,engine):
    bill = retrieveFeatures(bill_type,bill_number,engine)
    output = np.zeros((2))
    output[0] = runModel(model,bill)
    output[1] = modelConf(model,bill)
    return output

def retrieveFeatures(bill_type,bill_number,engine):
    #pull a bill's features from postgresql server
    #query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"';"
    query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' LIMIT 1;"
    bill = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    return bill


def initModel(mtype):
    #load model
    if mtype == 'logreg':
        model_file = './legislatr/static/logreg_model_subjects.pkl' #logistic regression
    if mtype == 'forest':
        model_file = './legislatr/static/random_forest_model_subjects.pkl' #random forest
    mfile = open(model_file,'rb')
    model = pickle.load(mfile)
    mfile.close()
    return model
