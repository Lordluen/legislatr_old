"""
Reads data from lobbying contributions into a pandas dataframe.  Data directly
from the following source in it's raw XML format:

http://www.senate.gov/legislative/Public_Disclosure/contributions_download.htm
    - mynameisfiber (2016/05/11)
    - Ethan D. Peck (2016/06/06) (lordluen)
"""
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from tqdm import tqdm
from sqlCommands import append_to_database

from dateutil.parser import parse as DateParser
import os


DATADIR = "../Legis_data/contributions"
FIELD_SPECS={
    'year': int,
    'amount': float,
    'registrantid': int,
    'received': DateParser,
    'contributiondate': DateParser,
    'contributiontype': str,
    'honoree': str,
}


def _dict_lower_keys(d):
    #turns all keys in dictionary into lowercase.
    return {k.lower():v for k,v in d.items()}

def parse_contribution_filing(fd):
    dom = ET.fromstring(fd.read())
    counter = 0
    data = {}
    data_topush = {}
    alldat = pd.DataFrame()
    #loop over each filing
    for filing in tqdm(dom.findall('.//Filing')):
        #loop over registrant for filing (should only be one).
        for reg in filing.findall('.//Registrant'):
            #loop over each contribution made in the filing.
            for child in filing.findall('.//Contribution'):
                data.clear()
                data_topush.clear()
                #load up the data dictionary with all info.
                data.update(_dict_lower_keys(filing.attrib))
                data.update(_dict_lower_keys(child.attrib))
                data.update(_dict_lower_keys(reg.attrib))
                #pull only the data I care about.
                data_topush = {key:cast(data[key]) for key,cast in FIELD_SPECS.items()}
                #load into a dataframe. this is slow and can be made better if I find the time.
                for key,cast in FIELD_SPECS.items():
                    alldat.loc[counter,key] = cast(data[key])
                counter = counter + 1
    #where data is N/A convert to -999 for missing data.
    #alldat.fillna(-999)
    #alldat.head(20)
    #alldat[alldat['year'] == 'N/A'] = -999
    #alldat[alldat['registrantid'] == 'N/A'] = -999
    #force ints to be ints.
    alldat['year'] = alldat['year'].astype(int)
    alldat['registrantid'] = alldat['registrantid'].astype(int)
    return alldat
                


def read_contribution_filings(datadir, dbname, engine, start_year=None):
    #this will read in and save out to a sql table rather than a dictionary.
    for filename in os.listdir(datadir):#tqdm(os.listdir(datadir)):
        if filename.endswith('.xml'):
            year = int(filename.split('_')[0])
            if start_year and year >= start_year:
                abspath = os.path.join(datadir, filename)
                print(abspath)
                with open(abspath) as fd:
                    filedata = parse_contribution_filing(fd) #get contributions from file as pd.df.
                    append_to_database(dbname,'contrib',filedata,engine)
    return


def contribution_filings(dbname,engine,datadir=DATADIR, start_year=None):
    #new version meant to be used with postgresql.
    print('please print this')
    read_contribution_filings(datadir, dbname, engine, start_year)
    print('leaving contribution_filings')
    return

if __name__ == "__main__":
    contribution_filings()
    print("\nSample result:")
    print(data[data['contributiontype'] == 'FECA'][['honoree', 'amount']] \
            .groupby('honoree') \
            .aggregate(np.sum) \
            .query('amount > 10') \
            .sort('amount'))
