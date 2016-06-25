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

app.var= {}

@app.route('/')
@app.route('/index')
@app.route('/input')
def legislatr_input():
    return render_template("input.html")

@app.route('/input2')
def legislatr_input2():
    congress = request.args.get('congress')
    app.var['congress'] = congress
    return render_template("input2.html",congress=congress)

@app.route('/input3')
def legislatr_input3():
    bill_type = request.args.get('bill_type')
    congress = request.args.get('congress')
    app.var['bill_type'] = bill_type
    app.var['congress'] = congress
    bill_list = list(map(int,legis_funcs.get_bills_list(bill_type,congress,db)))
    bill_list.sort()
    bill_list = list(map(str,bill_list))
    app.var['bill_list'] = bill_list
    return render_template("input3.html", congress=congress, bill_type=bill_type, bill_list=bill_list)

@app.route('/input4')
def legislatr_input4():
    bill_type = app.var['bill_type']
    congress = app.var['congress']
    bill_list = app.var['bill_list']
    bill_number = request.args.get('bill_number')
    app.var['bill_number'] = bill_number
    title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    app.var['title'] = title
    return render_template("input4.html", congress=congress, bill_type=bill_type, bill_list=bill_list, bill_title=title, bill_number=bill_number)

@app.route('/inputSearch')
def legislatr_inputSearch():
    query = request.args.get('query')
    query_db = legis_funcs.get_query_matches(query,db)
    app.var["query_db"] = query_db
    options = query_db["congress"].str.cat(query_db["bill_type"],sep=' : ').str.cat(query_db["bill_number"],sep=' : ').tolist()
    app.var["options"] = options
    return render_template("inputSearch.html", bill_options = options)

@app.route('/inputSearch2')
def legislatr_inputSearch2():
    ind = int(request.args.get('user_choice'))
    options = app.var["options"]
    option = options[ind]
    query_db = app.var["query_db"]
    congress = query_db["congress"].iloc[ind]
    bill_type = query_db["bill_type"].iloc[ind]
    bill_number = query_db["bill_number"].iloc[ind]
    title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    app.var['title'] = title
    app.var['bill_type'] = bill_type
    app.var['bill_number'] = bill_number
    app.var['congress'] = congress
    return render_template("inputSearch2.html", bill_choice=ind, congress=congress, bill_type=bill_type,bill_number=bill_number,bill_title=title,bill_options=options)


@app.route('/about')
def legislatr_about():
    return render_template("about.html")

@app.route('/output')
def legislatr_output():
    #pull 'birth_month' from input field and store it
    #bill_type = request.args.get('bill_type')
    #congress = request.args.get('congress')
    #if bill_type is None:
    bill_type = app.var['bill_type']
    #if congress is None:
    congress = app.var['congress']
    #bill_number = request.args.get('bill_number')
    bill_number = app.var['bill_number']

    model = legis_funcs.initModel('forest')
    #retrieve the bill information
    bill = legis_funcs.getBill(bill_type,bill_number,congress,db)
    result = legis_funcs.runModel(model,bill)
    if result[0] == 1:
        the_result = "PASS"
    if result[0] == 0:
        the_result = "FAIL"
    app.var['the_result'] = the_result
    the_confidence = legis_funcs.modelConf(model,bill)
    app.var['the_confidence'] = the_confidence
    if the_result == "PASS":
        img_file = 'glyphicon-ok'
        img_color = 'green'
    if the_result == "FAIL":
        img_file = 'glyphicon-remove'
        img_color = 'red'
    app.var['img_file'] = img_file
    app.var['img_color'] = img_color
    #title = legis_funcs.retrieveTitle(bill_type,bill_number,congress,db)
    title = app.var['title']
    funding_tup = legis_funcs.retrieveFunding(bill_type,bill_number,congress,db)
    legis_funcs.makeBarPlotFile(funding_tup,0) #for now just do the top ranked funder (rank = 0)
    top_five_funders = list()
    for x in range(0,5):
        top_five_funders.append(funding_tup[2][x][1]) #the names of the top 5 contributors.
    app.var['top_five_funders'] = top_five_funders
    app.var['funding_tup'] = funding_tup
    return render_template("output.html",the_result = the_result,
        the_confidence = int(round(the_confidence)),
        funders = top_five_funders,
        img_file = img_file, img_color = img_color,
        bill_title = title,
        bill_type=bill_type, bill_number=bill_number, congress=congress)

@app.route('/output2')
def legislatr_output2():
    bill_type = app.var['bill_type']
    bill_number = app.var['bill_number']
    congress = app.var['congress']
    img_file = app.var['img_file']
    img_color = app.var['img_color']
    the_confidence = app.var['the_confidence']
    the_result = app.var['the_result']
    top_five_funders = app.var['top_five_funders']
    funding_tup = app.var['funding_tup']
    title = app.var['title']
    funder = int(request.args.get('contributor'))
    legis_funcs.makeBarPlotFile(funding_tup,funder)
    return render_template("output2.html",the_result=the_result,
        the_confidence = int(round(the_confidence)),
        funders = top_five_funders,
        fund = funder,
        img_file = img_file, img_color= img_color,
        bill_title = title,
        bill_type=bill_type, bill_number=bill_number,congress=congress)
