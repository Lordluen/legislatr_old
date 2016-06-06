## Usage

First you have to download all the data,

```
$ ./getdata.sh
```

And then go grab a coffee... and then probably lunch.

Now you're ready to start playing with data!  The main file to be using is
`associate_contributions.py`.  It will load up all the contribution and votes
data and join them together.  Right now it limits itself to only votes that have
happened in 2016 so that the load time is quick, but this can be changed by
modifying the `start_year` parameter.


## Exploration Into Political Contributions

- [x] Read in contribution data ([contributions.py](contributions.py))
- [x] Read in legislator metadata ([legistlators.py](legistlators.py))
    - ~Code written and it works, but numbers seem a bit lot... why??~
- [x] Read in votes data ([votes.py](votes.py))
- [ ] Correlate honorees in contributions to legislators in voting data
    - Votes data uses the `bioguide` id which we index on in [legistlators.py](legistlators.py)
    - We'll need to do fuzzy searching... maybe remove common phrases (senator,
      sen., sir, ms, etc..) and then do best edit distance?
