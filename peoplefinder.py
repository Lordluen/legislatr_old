from fuzzywuzzy import process
from collections import namedtuple


Person = namedtuple('Person', 'name data score'.split())


class PeopleFinder(object):
    def __init__(self, yellow_pages):
        self.yellow_pages = yellow_pages
        self._names = list(yellow_pages.keys())

    def __call__(self, name, limit=1):
        results = process.extract(name, self._names, limit=limit)
        for name, score in results:
            yield Person(name, self.yellow_pages[name], score)

    def find_best(self, name):
        name, score= process.extractOne(name, self._names)
        return Person(name, self.yellow_pages[name], score)
