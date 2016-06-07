"""
Reads data from lobbying contributions into a pandas dataframe.  Data directly
from the following source in it's raw XML format:

http://www.senate.gov/legislative/Public_Disclosure/contributions_download.htm
    - mynameisfiber (2016/05/11)
"""
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm

from dateutil.parser import parse as DateParser
import os


DATADIR = "../Legis_data/contributions"
FIELD_SPECS={
    'year': int,
    'amount': float,
    'registrantid': int,
    'clientid': int,
    'received': DateParser,
    'contributiondate': DateParser,
}


def _dict_lower_keys(d):
    return {k.lower():v for k,v in d.items()}


def parse_contribution_filing(fd):
    dom = ET.fromstring(fd.read())
    data = {}
    for filing in tqdm(dom.findall('.//Filing')):
        for child in filing.findall('.//Contribution'):
            data.clear()
            data.update(_dict_lower_keys(filing.attrib))
            data.update(_dict_lower_keys(child.attrib))
            for key, cast in FIELD_SPECS.items():
                try:
                    data[key] = cast(data[key])
                except KeyError:
                    pass
            yield data


def read_contribution_filings_one(datadir, dbname, username, engine, start_year=None):
    #this will read in and save out to a sql table rather than a dictionary.
    for filename in tqdm(os.listdir(datadir)):
        if filename.endswith('.xml'):
            year = int(filename.split('_')[0])
            if start_year and year >= start_year:
                abspath = os.path.join(datadir, filename)
                with open(abspath) as fd:
                    filedata = parse_contribution_filing(fd) #get contributions from file.
                    data = pd.DataFrame.from_dict(filedata)  #save contributions in pandas dataFrame.
                    append_to_database(dbname,'contrib',data,engine)
    return


def read_contribution_filings(datadir, start_year=None):
    for filename in tqdm(os.listdir(datadir)):
        if filename.endswith('.xml'):
            year = int(filename.split('_')[0])
            if start_year and year >= start_year:
                abspath = os.path.join(datadir, filename)
                with open(abspath) as fd:
                    filedata = parse_contribution_filing(fd)
                    yield from filedata


#def contribution_filings(datadir=DATADIR, start_year=None):
#    raw_filings = read_contribution_filings(datadir, start_year)
#    data = pd.DataFrame.from_dict(raw_filings)
#    for field in ('contributiontype', 'honoree', 'id', 'contributor', 'type',
#                  'payee', 'period'):
#        data[field] = data[field].astype('category')
#    print('leaving contribution_filings')
#    return data

def contribution_filings(datadir=DATADIR, start_year=None):
    #new version meant to be used with postgresql.
    raw_filings = read_contribution_filings(datadir, start_year)
    data = pd.DataFrame.from_dict(raw_filings)
    #for field in ('contributiontype', 'honoree', 'id', 'contributor', 'type',
    #              'payee', 'period'):
    #    data[field] = data[field].astype('category')
    print('leaving contribution_filings')
    return data

if __name__ == "__main__":
    data = contribution_filings()
    print("\nSample result:")
    print(data[data['contributiontype'] == 'FECA'][['honoree', 'amount']] \
            .groupby('honoree') \
            .aggregate(np.sum) \
            .query('amount > 10') \
            .sort('amount'))
