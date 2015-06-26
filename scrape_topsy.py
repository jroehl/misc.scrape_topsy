#!/usr/bin/env python3
"""
Script for scraping topsy website.

Functions:
- Navigate to topsy URL passed as parameter
- Grab tweet details (TweetID, TweetText (including Hashtags, Links etc.), TweetTimestamp, InReplyTo ID)
- Open www.gettwitterid.com at the end of the run to obtain twitter id
- Save the details in standard scheme of tweets (adding None, or -1 for not yet obtained details)
"""

import re
import csv
import sys
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains


def new_set():
    """ Create new set."""
    # only needed because var = set() does throw an error if used in main method
    var = set()
    return var


def scrape(arg):
    """ Create new set."""
    # if link does not start with "http://", it is added
    if not arg.startswith('http://'):
        arg = "http://{0}" .format(arg)

    # new browser driver instance for Firefox
    browser = webdriver.Firefox()
    # implicit wait for sites to load
    browser.implicitly_wait(2.5)
    # navigate to page
    browser.get("{0}" .format(arg))

    # grabbed tweet count
    count = 0
    # dictionary for storing the details and script data

    tweets = []

    # header for the csv file
    header = ["TweetID",
              "TwitterID",
              "CreatedAt",
              "Language",
              "Truncated",
              "Source",
              "Coordinates",
              "RepUserID",
              "RetweetCount",
              "FavoriteCount",
              "Text",
              ]

    # headerrow is appended as first entry
    tweets.append(header)

    collection = {"tweets": tweets,
                  "count": count,
                  "errors": {"count": 0, "text": []}}
    # the length of the "tweet_id" set (unique) of the previous run is stored in old_len for comparison with the new_len
    old_len = 10
    new_len = 0
    # if the lenghts of the sets are equal, no new data has been obtained
    while old_len != new_len:

        old_len = len(collection["tweets"])
        new_collection = scrape_topsy(browser, collection)
        new_len = len(new_collection["tweets"])
        print(old_len, new_len)
        # break out of while loop to avoid duplicates
        if old_len == new_len:
            break

        # if new results are found result is stored in the main dictionary
        collection = new_collection

        count = collection["count"]

        # Try to find the "next" button on topsy page for navigation
        xpath = "//*[@id='module-pager']/div/ul/li[12]/a"
        for counter in range(3):
            # page_has_loaded() method returns true (false) if xpath is (not) found
            if not page_has_loaded(browser, xpath):
                # if this happens twice, URL is probably not a topsy URL
                if counter == 2:
                    log("\"{1}\" - is not a topsy URL" .format(time.ctime(), arg, e))
                    sys.exit(0)
                # browser is refreshed for new try
                browser.refresh()
            else:
                break

        # next button is located and clicked for new result page
        next_btn = browser.find_element_by_xpath(xpath)
        next_btn.click()

        time.sleep(2)

    # navigate to URL to obtain the twitterID by the twitterName
    browser.get("http://gettwitterid.com/")
    name = collection["tweets"][1][1]
    search_bar = browser.find_element_by_xpath("//*[@id='search_bar']")
    search_bar.send_keys(name)
    search_bar.send_keys(Keys.RETURN)
    real_id = browser.find_element_by_xpath("/html/body/div/div[1]/table/tbody/tr[1]/td[2]/p").text

    # overwrite the twitterName by the twitterID
    for entry in collection["tweets"]:
        if entry[1] != "TwitterID":
            entry[1] = real_id

    # save the errorcount and errortexts in temp variables
    errorcount = collection["errors"]["count"]
    errortexts = collection["errors"]["text"]

    # output as csv
    write_to_CSV(name, collection["tweets"])

    # close the current firefox driver instance
    browser.quit()

    # write logs for output through applescript notification
    if errorcount == 0:
        log("{0}\n{1} tweets scraped and saved to {2}.csv.." .format(time.ctime(), count+1, name))
    elif errorcount > 0:
        log("{0}\n{1} tweets scraped with errors and saved to {2}.csv.." .format(time.ctime(), count+1, name))
        errorlog("{0}\n{1} errors on following results:" .format(time.ctime(), errorcount))
        for errortext in errortexts:
            errorlog("\n{0}\n" .format(errortext))


def scrape_topsy(browser, collection):
    """Scrape the browser page_source."""
    # get the whole content of page
    html_source = browser.page_source

    # BeautifulSoup find only the media body tag
    soup = BeautifulSoup(html_source)
    results = soup.find_all("div", class_="result-tweet")
    count = 0
    for result in results:
        count += 1
        try:

            # navigate to right div and get_text()
            soup = result.div.div
            text = soup.div.get_text()

            # find <a> with twitter_id and strip ID
            twitter_id = result.find("a")['href']
            twitter_id = re.search('(?<=twitter.com/).*', str(twitter_id)).group()

            # try to obtain the reply_to, if not found catch group().. exception and set rep_to = 0
            try:
                rep_to = re.search('(?<=in_reply_to=)\d+', str(soup.ul.li.next_sibling)).group()
            except:
                rep_to = 0

            soup = soup.ul.li.small.a

            # find tweet_id and strip ID
            tweet_id = re.search('(?<=status/)\d+', str(soup['href'])).group()

            # find date as epoch time and convert to formatted date
            created_at = soup.span.next_element.next_element['data-timestamp']
            created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(created_at)))

            # counts = browse_twitter(browser, result, count)
            counts = [-1, -1]
            # save results to the dictionary, append None, or default values if not found
            tweet = [tweet_id, twitter_id, created_at, None, False, None, None, rep_to, counts[0], counts[1], text]

            for stored_tweet in collection["tweets"]:
                if tweet[0] in stored_tweet:
                    raise Exception

            collection["tweets"].append(tweet)

        # catch exception of run, store errorcount increment and resulttext in dictionary["errors"]
        except Exception as e:
            print(e)
            collection["errors"]["count"] += 1
            collection["errors"]["text"].append("\n{0}\n{1}" .format(result, tweet))

    collection["count"] = count
    return collection


def page_has_loaded(browser, xpath):
    """Find out if page element could be found(page has loaded)."""
    # returns true or false
    try:
        # sleep for half a second
        time.sleep(0.5)
        # try to find element
        browser.find_element_by_xpath(xpath)
        return True
    except:
        # catch ElementNotFoundException (page has not loaded)
        return False


def browse_twitter(browser, result, count):
    """Open tweet page on twitter.com according to found tweet ID on topsy.com."""
    try:
        # save current handle in variable
        main_window = browser.current_window_handle
    except Exception as e:
        # catch if not found
        errorlog("\n{0} current_window_handle" .format(e))
        # return default value
        return [-1, -1]

    # problem of skipped tweets is handled
    # count for finding xpath is incremented, for other results than, tweets
    if count >= 6:
        count += 1
    try:
        tweet = browser.find_element_by_xpath("//*[@id='results']/div[{0}]/div/div/ul/li[1]/small/a/span[2]" .format(count))
    except:
        # if element not found return default value
        return [-1, -1]

    # action chain command + click to open twitter.com in new tab
    action = ActionChains(browser)
    action.key_down(Keys.COMMAND)
    action.click(tweet)
    action.key_up(Keys.COMMAND)
    action.perform()

    # switch to new tab control + tab
    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.TAB)

    # Different approach to handle page not loaded
    # Try
    # WebDriverWait(browser, 10).until(
    #     EC.presence_of_element_located((By.XPATH, "//*[@id='doc']"))
    # )

    # try for 3 time to find the element on page (if page load was not fast enough)
    for counter in range(3):
        if not page_has_loaded(browser, "//*[@id='doc']"):
            if counter == 2:
                # after 3 tries return default value
                browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
                browser.switch_to_window(main_window)
                return [-1, -1]
            browser.refresh()

    # get the current browser content (of new tab)
    html_source = browser.page_source
    soup = BeautifulSoup(html_source)
    # find part with retweet and favorite count number
    retweet_count = soup.find_all(class_="request-retweeted-popup")
    # try to find retweet count if not return default
    try:
        retweet_count = re.search('(?<=<strong>)\d+', str(retweet_count)).group()
    except:
        retweet_count = -1
    favorite_count = soup.find_all(class_="request-favorited-popup")
    # try to find favorite count if not return default
    try:
        favorite_count = re.search('(?<=<strong>)\d+', str(favorite_count)).group()
    except:
        favorite_count = -1

    # focus on current main page (current tab) and close command + w
    browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')

    # switch focus to original (main) window handle
    browser.switch_to_window(main_window)

    return [retweet_count, favorite_count]


def tweet_regex(string):
    """Strip tweet from html codes."""
    tweet = re.sub('==.jsp', '', string)
    tweet = re.sub('<div>', '', tweet)
    tweet = re.sub('</div>', '', tweet)
    tweet = re.sub('<a data-hashtag=', ' ', tweet)
    tweet = re.sub('<a data-username=', ' ', tweet)
    tweet = re.sub('<a href=', ' ', tweet)
    tweet = re.sub('href=.*?(>)', '', tweet)
    tweet = re.sub('</a>', ' ', tweet)
    tweet = re.sub('>pic.twitter.com.*', ' ', tweet)
    tweet = re.sub('"', '', tweet)

    return tweet


def write_to_CSV(name, lists):
    """Write the tweets to a CSV file."""
    # create directory (if not exists) temp_csv on desktop
    desktop_path = "{0}/Desktop" .format(os.getcwd().replace("/scripts", ""))
    mk_dir("temp_csv")
    filename = '{0}/temp_csv/{1}.csv' .format(desktop_path, name)

    try:
        # write the csv
        with open('{0}' .format(filename), 'a') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerows(lists)
    except Exception as e:
        log("{0} : Problem writing to file" .format(e))


def log(output):
    """Write a log file into script directory."""
    with open("{0}/temp.log" .format(os.getcwd()), "a") as log:
        log.write("{0}\n" .format(output))


def errorlog(output):
    """Write an errorlog file into script directory."""
    with open("{0}/error.log" .format(os.getcwd()), "a") as log:
        log.write("{0}\n" .format(output))


def mk_dir(dirname):
    """Try to create directory, pass if it fails."""
    try:
        os.makedirs('{0}/Desktop/{1}' .format(os.getcwd().replace("/scripts", ""), dirname))
    except:
        pass


if __name__ == "__main__":
    """Checks if no parameter is passed"""
    try:
        scrape(sys.argv[1])
    except Exception as e:
        log("Error starting script:\n{0}" .format(e))
