# README #

This README documents whatever steps are necessary to get your application up and running.

### run script ###

* start the script by right clicking link and selecting service in browser (preferably NOT firefox)

### What is this repository for? ###

* Script for scraping topsy tweets
      - opens webpage
      - gets all tweet content (10 per page)
      - opens for every tweet the twitter page of tweet and tries to get retweet and favorite count
      - works through following pages until end of results is reached
      - saves tweets to twittername.csv in /Users/username/desktop/temp_csv

     

* 2015/06/23 Version 0.1

### How do I get set up? ###

* "scrape_topsy.py" python 3 script has to be put to "/Users/USERNAME/scripts" / "~/scripts"
      - ideally clone this repository to this path

* Script needs:
      - beautifulsoup   (pip3 install beautifulsoup4)
      - selenium	(pip3 install selenium)

* Installation of Firefox required:
      - tested with vers. 38.0.5

* "Scrape Topsy URL.workflow" has to be installed (and updated) manually as service for mac

* "~/.bash_profile" exists:
      - check with:
      - "nano ~/.bash_profile" and/or "echo $PATH"
      - ($PATH has variables for python and shell/bash set)

      - at least following entry exists:
            # Setting PATH for Python 3.4
            # The orginal version is saved in .bash_profile.pysave
            PATH="/Library/Frameworks/Python.framework/Versions/3.4/bin:${PATH}"
            export PATH
            
      - maybe the entry has to be altered for python3.4 path on current machine

* script creates folder (if not exists) "/Users/USERNAME/Desktop/temp_csv/" where the csv file (name=twitter_name) will be put

### TODO ###

* Full comments in script
* ...
