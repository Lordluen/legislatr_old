"""
Read in legistlator metadata from
https://github.com/unitedstates/congress-legislators and filter down/index on
bioguide id for later correlation
    - mynameisfiber (2016/05/11)
"""
import pandas as pd
import yaml
from tqdm import tqdm

import os


DATADIR = './data/congress-legislators/'


def parse_legislators(data, start_year=None):
    for legis in tqdm(data):
        if start_year:
            most_recent_term= max(int(t['end'].split('-', 1)[0])
                                  for t in legis['terms'])
            if  most_recent_term < start_year:
                continue
        yield (legis['id']['bioguide'], legis)


def read_legistlators(fd, start_year=None):
    curdata = yaml.load(fd)
    yield from parse_legislators(curdata, start_year=start_year)


def legistlators(datadir=DATADIR, start_year=None):
    datafiles = ['legislators-current.yaml', 'legislators-historical.yaml']
    data = {}
    for datafile in tqdm(datafiles):
        abspath = os.path.join(datadir, datafile)
        with open(abspath) as fd:
            new_data = read_legistlators(fd, start_year)
            data.update(new_data)
    return data


if __name__ == "__main__":
    data = legistlators(start_year=2008)
