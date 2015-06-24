#!/usr/bin/env python3

import re
import csv
import sys
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def new_set():
    var = set()
    return var


def scrape(arg):

    # return arg
    # lists = scrape()
    # write_to_CSV("scraped", lists)
    if not arg.startswith('http://'):
        arg = "http://{0}" .format(arg)

    browser = webdriver.Firefox()
    browser.implicitly_wait(2.5)
    browser.get("{0}" .format(arg))
    # browser.get('http://topsy.com/s?q=from%3ALOTR&mintime=1388617248')
    count = 0
    dic = {  # 10
           "tweet_id": new_set(),
             # 11
           "twitter_id": [],
             # 2
           "created_at": [],
             # 4
           "language": [],
             # 9
           "truncated": [],
             # 7
           "source": [],
             # 1
           "coordinates": [],
             # 5
           "reply_user_id": [],
             # 6
           "retweet_count": [],
             # 3
           "favorite_count": [],
             # 8
           "text": [],
           "count": count
           }

    while count % 10 == 0:
        old_len = len(dic["tweet_id"])
        new_dic = scrape_topsy(browser, dic)
        new_len = len(new_dic["tweet_id"])
        if old_len == new_len:
            break
        dic = new_dic
        count = dic["count"]
        xpath = "//*[@id='module-pager']/div/ul/li[12]/a"
        for counter in range(3):
            if not page_has_loaded(browser, xpath):
                if counter == 2:
                    log("{0}\nNot a topsy URL specified:\n{1}" .format(arg, e))
                    sys.exit(0)
                browser.refresh()
            if page_has_loaded(browser, xpath):
                break

        next_btn = browser.find_element_by_xpath(xpath)
        next_btn.click()

    dic["tweet_id"] = list(dic["tweet_id"])

    header = ["Coordinates",
              "CreatedAt",
              "FavoriteCount",
              "Language",
              "RepUserID",
              "RetweetCount",
              "Source",
              "Text",
              "Truncated",
              "TweetID",
              "TwitterID"
              ]

    write_list = []
    write_list.append(header)

    browser.get("http://gettwitterid.com/")
    name = dic["twitter_id"][0]
    search_bar = browser.find_element_by_xpath("//*[@id='search_bar']")
    search_bar.send_keys(name)
    search_bar.send_keys(Keys.RETURN)

    result = browser.find_element_by_xpath("/html/body/div/div[1]/table/tbody/tr[1]/td[2]/p").text

    dic["twitter_id"] = [result for item in dic["twitter_id"]]

    del dic["count"]
    for count in range(len(dic["tweet_id"])):
        write_list.append([dic[key][count] for key in sorted(dic)])

    write_to_CSV(name, write_list)

    browser.quit()

    log("{0} tweets scraped and saved to {1}.csv.." .format(count+1, name))


def scrape_topsy(browser, set):

    html_source = browser.page_source

    soup = BeautifulSoup(html_source)
    results = soup.find_all("div", class_="media-body")

    count = 0
    for result in results:
        count += 1

        text = result.find("div")
        text = tweet_regex(str(text))

        twitter_id = result.find("a")
        twitter_id = re.search('(?<=twitter.com/).*?(")', str(twitter_id)).group()
        twitter_id = twitter_id.replace("\"", "")

        muted = result.find_all("a", class_="muted")

        rep_to = re.search('(?<=status/)\d+', str(muted)).group()

        tweet_id = re.search('(?<=status/)\d+', str(muted)).group()

        created_at = re.search('(?<=timestamp=")\d+', str(muted)).group()
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(created_at)))

        counts = browse_twitter(browser, result, count)

        set["tweet_id"].add(tweet_id)
        set["twitter_id"].append(twitter_id)
        set["created_at"].append(created_at)
        set["language"].append(None)
        set["truncated"].append(False)
        set["source"].append(None)
        set["coordinates"].append(None)
        set["reply_user_id"].append(rep_to)
        set["retweet_count"].append(counts[0])
        set["favorite_count"].append(counts[1])
        set["text"].append(text)
        set["count"] = count

    return set


def page_has_loaded(browser, xpath):
        try:
            time.sleep(0.5)
            browser.find_element_by_xpath(xpath)
            return True
        except:
            return False


def browse_twitter(browser, result, count):

    try:
        main_window = browser.current_window_handle
    except Exception as e:
        log("{0} current_window_handle" .format(e))
        return [-1, -1]

    if count >= 6:
        count += 1
    try:
        tweet = browser.find_element_by_xpath("//*[@id='results']/div[{0}]/div/div/ul/li[1]/small/a/span[2]" .format(count))
    except:
        try:
            tweet = browser.find_element_by_xpath("//*[@id='results']/div[{0}]/div/div/ul/li[1]/small/a/span[2]" .format(count+1))
        except:
            return [-1, -1]

    action = ActionChains(browser)
    action.key_down(Keys.COMMAND)
    action.click(tweet)
    action.key_up(Keys.COMMAND)
    action.perform()

    browser.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.TAB)

    # Try
    # WebDriverWait(browser, 10).until(
    #     EC.presence_of_element_located((By.XPATH, "//*[@id='doc']"))
    # )

    for counter in range(3):
        if not page_has_loaded(browser, "//*[@id='doc']"):
            if counter == 2:
                # header = browser.find_element_by_xpath("/html/body/div[2]/div/h1").text
                browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')
                browser.switch_to_window(main_window)
                return [-1, -1]
            browser.refresh()

    html_source = browser.page_source
    soup = BeautifulSoup(html_source)
    retweet_count = soup.find_all(class_="request-retweeted-popup")
    try:
        retweet_count = re.search('(?<=<strong>)\d+', str(retweet_count)).group()
    except:
        retweet_count = -1
    favorite_count = soup.find_all(class_="request-favorited-popup")
    try:
        favorite_count = re.search('(?<=<strong>)\d+', str(favorite_count)).group()
    except:
        favorite_count = -1

    browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 'w')

    browser.switch_to_window(main_window)

    return [retweet_count, favorite_count]


def tweet_regex(string):
    tweet = re.sub('http://.*?(==.jsp)', '', string)
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
    with open("{0}/temp.log" .format(os.getcwd()), "a") as log:
        log.write("{0}\n" .format(output))


def mk_dir(dirname):
    """Try to create directory, pass if it fails."""
    try:
        os.makedirs('{0}/Desktop/{1}' .format(os.getcwd().replace("/scripts", ""), dirname))
    except:
        pass


if __name__ == "__main__":
    try:
        scrape(sys.argv[1])
    except Exception as e:
        log("Error starting script:\n{0}" .format(e))
