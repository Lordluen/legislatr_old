"""
Read in bill information from https://www.govtrack.us/data/congress/ (info at https://www.govtrack.us/developers/data)
Written By,
Ethan D. Peck
"""
import numpy as np
import pandas as pd
import ujson as json
from tqdm import tqdm

from dateutil.parser import parse as DateParser
import os

DATADIR = './data/votes/'


def get_votes_files(datadir=DATADIR, start_year=None):
    for congress in tqdm(os.listdir(datadir)):
        if not congress.isnumeric():
            continue
        congress_path = os.path.join(datadir, congress, 'votes/')
        for year in os.listdir(congress_path):
            try:
                if start_year and int(year) < start_year:
                    continue
            except ValueError:
                continue
            year_path = os.path.join(congress_path, year)
            for bill in tqdm(os.listdir(year_path)):
                yield os.path.join(year_path, bill, "data.json")

def parse_votes_useful_info(fd):
    data = json.load(fd)
    if 'bill' not in data:
        return
    bill_info = {
        "type": data['bill']['type'],
        "number": data['bill']['number'],
        "congress": data['bill']['congress'],
        "category": data['category'],
        "chamber": data['chamber'],
        "date": DateParser(data['date']),
        "result": data['result'],
    }
    return bill_info

def parse_bills(info, datadir=DATADIR):
    bill_path = os.path.join(datadir,
        str(info['congress']),'bills/',info['type'],(info['type']+str(info['number'])),"data.json")
    data = json.load(open(bill_path))
    info['subjects']=tuple(data['subjects'])
    info['top_subject']=data['subjects_top_term']
    yield info

def read_bills(datadir=DATADIR, start_year=None):
    #this will read in bills
    votes_files = get_votes_files(datadir, start_year)
    for votefile in votes_files:
    #only want bills that get to a vote. So first find the vote file to get a bill number.
        with open(votefile) as fd:
            try:
                useful_info = parse_votes_useful_info(fd) #get bill info from vote file
                yield from parse_bills(useful_info) #parse bill using info from prev line.
            except (KeyError, TypeError) as e:
                pass

def bills( datadir=DATADIR, start_year=None ):
    #this will read in bills
    raw_bills = read_bills( datadir, start_year )
    print('not that far')
    data = pd.DataFrame.from_dict( raw_bills )
    print('made it this far')
    return data
    for field in ( 'type', 'number', 'congress', 'category', 
                   'chamber', 'date', 'subjects', 'top_subject', 'result'):
        data[field] = data[field].astype('category')
    print('leaving bills')
    return data
