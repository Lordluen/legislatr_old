import contributions
import votes
from peoplefinder import PeopleFinder

from operator import attrgetter


def associate_names(people_finder):
    def _(name):
        if name.lower() == 'n/a':
            return None
        fullname = people_finder.find_best(name)
        lastname = people_finder.find_best(name.split(' ')[-1])
        best_result = max((fullname, lastname), key=attrgetter('score'))
        return best_result.data
    return _


def associated_contributions(start_year):
    contrib_df = contributions.contribution_filings(start_year=start_year)
    contrib_df = contrib_df[contrib_df['honoree'] != 'N/A']
    earliest_year = contrib_df['received'].min().year
    
    votes_df = votes.votes(start_year=earliest_year)
    yellow_pages = votes_df.set_index('display_name')['id'].to_dict()
    people_finder = PeopleFinder(yellow_pages)

    contrib_df['id_honoree'] = (contrib_df['honoree']
        .apply(associate_names(people_finder))
        .astype('category'))
    return contrib_df


if __name__ == "__main__":
    contrib_df = associated_contributions(2016)
