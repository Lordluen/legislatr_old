#legis_funcs.py
#This will contain all of the functions used by the legislatr web-app.
#Created By, Ethan D. Peck

import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from sklearn import linear_model
from sklearn.ensemble import RandomForestClassifier
import pickle
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import re
import numpy as np

def runModel(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status','final_result','congress'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    result = model.predict(X)
    return result

def modelConf(model,bill):
    test_data = bill.drop(['bill_number','bill_type','index','result','status','final_result','congress'],axis=1)
    X = (test_data.as_matrix().flatten()).reshape(1,-1)
    P = model.predict_proba(X)
    #print(type(P[0]))
    #print(P[0][1])
    #print(P)
    #Pr = max(P[0])*100. #convert to percent
    Pr = P[0][1]*100.
    return Pr

def getBill(bill_type,bill_number,congress,engine):
    bill = retrieveFeatures(bill_type,bill_number,congress,engine)
    return bill 

def getResult(model,bill_type,bill_number,congress,engine):
    bill = retrieveFeatures(bill_type,bill_number,congress,engine)
    output = np.zeros((2))
    output[0] = runModel(model,bill)
    output[1] = modelConf(model,bill)
    return output

def retrieveFeatures(bill_type,bill_number,congress,engine):
    #pull a bill's features from postgresql server
    #query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"';"
    #query = "SELECT * FROM features WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' LIMIT 1;"
    query = "SELECT * FROM features_subs WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_subs = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    query = "SELECT * FROM features_legis WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_legis = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    query = "SELECT * FROM features_comms WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_comms = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    #fuse them
    bill = pd.concat([bill_subs,bill_legis.drop(['bill_number','bill_type','index','result','status','final_result','num_amends','congress'],axis=1),
                     bill_comms.drop(['bill_number','bill_type','index','result','status','final_result','num_amends','congress'],axis=1)],axis=1)
    return bill

def initModel(mtype):
    #load model
    #if mtype == 'logreg':
    #    model_file = './legislatr/static/logreg_model_subjects.pkl' #logistic regression
    if mtype == 'forest':
        model_file = './legislatr/static/random_forest_model_subs_legis_comms.pkl' #random forest
    mfile = open(model_file,'rb')
    model = pickle.load(mfile)
    mfile.close()
    return model

def pull_contributions(legis,legis_all,engine):
    #will return a datafram with all contributions to a given legislator
    #legis is the legislator dataframe
    #i is the row in question (legislator we care about)
    fname = legis.fname.iloc[0]
    lname = legis.lname.iloc[0]
    station = legis.station.iloc[0]
    name = legis.qsponsor.iloc[0]
    #clean name for query
    fname = re.sub("'","''",fname)
    lname = re.sub("'","''",lname)
    perfectQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+fname+"%%' AND honoree LIKE '%%"+lname+"%%' AND contributiontype LIKE 'FECA' ;" #definite
    lessQ = "SELECT * FROM contrib WHERE honoree LIKE '%%"+lname+"%%';" #definite + maybe
    perfectdf = pd.read_sql_query(perfectQ,engine)
    lessdf = pd.read_sql_query(lessQ,engine)
    maybedf = pd.concat([perfectdf,lessdf],axis=0).drop_duplicates(keep=False) #maybe

    finaldf = perfectdf #will concatanate successful matches
    #reduce total number of possible legislators to fuzzy
    fuzz_legis = legis_all[legis_all.lname == lname]['qsponsor'].tolist()

    #print(fuzz_legis)
    matchbool = list()
    matchstr = list()

    #reduce list if it addresses the wrong station
    if station == 'Rep':
        opp_station = 'Sen'
    if station == 'Sen':
        opp_station = 'Rep'
    bools = [not i for i in maybedf.honoree.str.contains(opp_station)] #if it contains opposing station, then not correct.
    maybedf2 = maybedf[bools]
    #maybedf2
    for c in range(maybedf2.index.size):
        con = maybedf2.honoree.iloc[c]
        match = process.extractOne(con,fuzz_legis)
        if (match[0] ==  name) and match[1] > 55:
            matchbool.append(1)
        else:
            matchbool.append(0)
    matchbool = np.array(matchbool).astype(bool)
    maybedf3 = maybedf2[matchbool]
    return maybedf3

def retrieveTitle(bill_type,bill_number,congress,engine):
    query = "SELECT otitle FROM bill_info WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    otitle = pd.read_sql_query(query,engine)["otitle"].iloc[0]
    return otitle

def retrieveFunding(bill_type,bill_number,congress,engine):

    query = "SELECT * FROM features_legis WHERE bill_type LIKE '"+bill_type+"' AND bill_number LIKE '"+bill_number+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_legis = pd.read_sql_query(query,engine) #note to self, bills repeat, I only want the most recent one.
    #drop useless columns.
    bill_legis = bill_legis.drop(['bill_type','bill_number','congress','num_amends','index','status','result','final_result'],1)
    #read in legislator info
    legis = pd.read_sql_table('sponsor_list_det',engine)

    cols = bill_legis.columns.tolist()
    mat = bill_legis.as_matrix().flatten().tolist()

    #list of legislators on bill
    legislators = list()
    for leg in range(0,len(cols)):
        if mat[leg] == 1:
                legislators.append(cols[leg])
    #loop through legislators and get funding df for each one, stored in a list.
    legis_funds = list()
    legis_names = list()
    for leg in legislators:
        #first get row in legis
        legis_ind = legis[legis.sponsor == leg]
        if legis_ind['index'].size > 1: #something has gone wrong.
            print('Something has gone wrong.')
            break
        legis_funds.append(pull_contributions(legis_ind,legis,engine))
        legis_names.append(legis_ind.qsponsor.iloc[0])
    allfunds = list()
    allcontribs = list()
    #do what I need with one dataframe first
    counter = 0
    for df in legis_funds :
        #sum up contributions from the same contributers
        u_reg = np.unique(df.registrantid) #all unique contributors
        allcontribs.append(u_reg)
        u_reg_name = list() #name of contributor
        u_reg_con = list() #sum of contributions
        for rid_ind in range(0,len(u_reg)):
            regid = u_reg[rid_ind] #id for contributor
            regname = df[df.registrantid == regid]['registrantname'].iloc[0]
            tot_money = np.sum(df[df.registrantid == regid]['amount'])
            u_reg_name.append(regname)
            u_reg_con.append(tot_money)
        u_reg = u_reg.tolist()
        temp_name = legis_names[counter]
        temp_name = [temp_name]*len(u_reg)
        allfunds.append(list(zip(u_reg,u_reg_name,u_reg_con,temp_name)))
        #print(allfunds[0][0])
        counter = counter+1
    #identify all shared contributors
    sharedcontribs = list()
    if len(allcontribs) == 1: #there is only one legislator
        sharedcontribs = allcontribs[0].tolist()
    else:
        for l1 in range(0,len(allcontribs)-1) : #loop over main list
            for item in allcontribs[l1] : #loop over all id numbers in main list
                for l2 in range(l1+1,len(allcontribs)): #loop over other lists to check for id number (item)
                    otherlist = allcontribs[l2]
                    if item in otherlist:
                        sharedcontribs.append(item)
                        break

    u_sharedcontribs = np.unique(sharedcontribs)
    shared_con = list() #list that will hold all contribution tuples that come from contributors that donate to other sponsors
    legislator_num = 0 #used to track which legislator the funds relate to.
    for rid in u_sharedcontribs : #go through registrant ids in shared contribs
        for l in allfunds: #list of all lists containing tuples of contributors
            for tup in l: #loop through each tupple in a list. #could be vectorized I bet
                if tup[0] == rid:
                    shared_con.append(tup)
                    break

    #loop over shared money to get total contributed from the shared contributors.
    tot_u_shared_contribs = list()
    for item in range(0,len(u_sharedcontribs)):
        tot = 0
        rid = u_sharedcontribs[item]
        for tup in shared_con:
            if tup[0] == rid:
                tot = tot + tup[2]
                name = tup[1] #could be placed in boolean to only occur once, but this is still not slow.
        tot_u_shared_contribs.append((rid,name,tot))
#sort to get the largest donators of the shared contributors
    tot_u_shared_contribs = sorted(tot_u_shared_contribs, key=lambda tup: tup[2], reverse=True)

    return (tot_u_shared_contribs,shared_con) #return the shared contributions (totals, indiv)

def makeBarPlotFile(contrib_tup,rank) :
    #plot the money distribution to individual senators by the largest contributor
    rid = contrib_tup[0][rank][0]
    name = contrib_tup[0][rank][1]
    total = contrib_tup[0][rank][2]
    toPlot = [x for x in contrib_tup[1] if x[0] == rid]
    #output to intermediate file
    x = list()
    y = list()
    for i in toPlot:
        x.append(i[3])
        y.append(i[2])
    with open("legislatr/static/data.tsv", "w") as record_file:
        record_file.write("Legislator\tContribution\n")
        for i in range(0,len(x)):
            record_file.write(str(x[i])+"\t"+str(y[i])+"\n")
    return

def get_bills_list(bill_type,congress,engine) :
    query = "SELECT bill_number FROM bill_info WHERE bill_type LIKE '"+bill_type+"' AND congress = '"+congress+"' ;" #should only be one match.
    bill_numbers = pd.read_sql_query(query,engine)["bill_number"].tolist()
    return bill_numbers
    
