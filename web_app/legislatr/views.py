from flask import render_template, request
from legislatr import app
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import pandas as pd
import psycopg2
import sqlCommands
import legis_funcs

dbname = 'legislatr'
db = sqlCommands.get_engine(dbname)

@app.route('/')
@app.route('/index')
@app.route('/input')
def legislatr_input():
    return render_template("input.html")

@app.route('/about')
def legislatr_about():
    return render_template("about.html")

@app.route('/output')
def legislatr_output():
    #pull 'birth_month' from input field and store it
    bill_type = request.args.get('bill_type')
    bill_number = request.args.get('bill_number')
    congress = request.args.get('congress')
    model = legis_funcs.initModel('forest')
    #retrieve the bill information
    bill = legis_funcs.getBill(bill_type,bill_number,congress,db)
    result = legis_funcs.runModel(model,bill)
    if result[0] == 1:
        the_result = "PASS"
    if result[0] == 0:
        the_result = "FAIL"
    the_confidence = legis_funcs.modelConf(model,bill)
    funding_tup = legis_funcs.retrieveFunding(bill_type,bill_number,congress,db)
    legis_funcs.makeBarPlotFile(funding_tup,0) #for now just do the top ranked funder (rank = 0)
    top_five_funders = list()
    for x in range(0,5):
        top_five_funders.append(funding_tup[0][x][1]) #the names of the top 5 contributors.
    return render_template("output.html",the_result = the_result,
        the_confidence = round(the_confidence,2),
        funders = top_five_funders)
