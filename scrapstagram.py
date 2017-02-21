
import argparse
import datetime
import os
import time
import yaml
from selenium import webdriver
from sys import platform

__author__ = "Edward Tran"
__version__ = "0.1.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://www.instagram.com/explore/tags"


class Scrapstagram:

    def __init__(self, headless="phantomjs", browser=None, webdriver_path=None):
        """
        Args:
            headless (str): Headless tool name.
            browser (str): Browser to run selenium.
            webdriver_path (str): Specific web driver path other than default.
        """

        with open(os.path.join(BASE_DIR, "config", "settings.yaml")) as file:
            self.settings = yaml.load(file)

        self.platform = "linux"

        if platform == "win32":
            self.platform = "windows"
        elif platform == "darwin":
            self.platform = "mac"

        if browser:
            self.webdriver_path = os.path.join(BASE_DIR, "webdrivers", self.platform, self.settings["webdrivers"][browser][self.platform])
        elif webdriver_path:
            self.webdriver_path = webdriver_path
        else:
            self.webdriver_path = os.path.join(BASE_DIR, "webdrivers", self.platform, self.settings["webdrivers"][headless][self.platform])

        if browser == "chrome":
            self.driver = webdriver.Chrome(self.webdriver_path)
        elif browser == "firefox":
            self.driver = webdriver.Firefox(self.webdriver_path)
        else:
            self.driver = webdriver.PhantomJS(self.webdriver_path)

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        self.driver.quit()

    def get_post_by_hashtag(self, hashtag, max_page=10, max_post=1000):
        """ Get post(s) by hashtags.

        Args:
            hashtag (str): Hashtag without '#'.
            max_page (int): Maximum page to scroll down on the web page before scrapping.
            max_post (int): Maximum number of post(s).

        Returns:
            list of post(s) dictionary with link, image, text, datetime, video, likes and views as keys.
        """

        start_dt = datetime.datetime.now()
        url = "{}/{}".format(BASE_URL, hashtag)
        self.driver.get(url)
        posts = list()
        errors = 0

        # Get "Load more" button
        button = self.driver.find_element_by_xpath("//a[contains(.,'Load more')]")
        button.click()

        for i in range(max_page):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")

            time.sleep(0.2)

            # Scroll to top
            self.driver.execute_script("window.scrollTo(0,(document.body.scrollHeight - 5000));")

            time.sleep(0.2)

        # Get all IG pictures
        elements = self.driver.find_elements_by_css_selector("article > div > div > div >  a")

        for element in elements:

            if len(posts) == max_post:
                break

            data = dict(
                link=element.get_attribute("href"),
                image=element.find_element_by_tag_name("img").get_attribute("src"),
                text=element.find_element_by_tag_name("img").get_attribute("alt"),
            )

            posts.append(data)

        for post in posts:
            # Go on IG picture link
            self.driver.get(post["link"])
            print("Post: {} ".format(post.get("link")))

            time.sleep(0.3)

            try:
                element = self.driver.find_element_by_css_selector("article > div > section > div")
            except:
                print("ERROR")
                print(post["link"])
                print(post["image"])
                print()
                errors += 1
                continue

            try:
                post["datetime"] = self.driver.find_element_by_tag_name("time").get_attribute("datetime")
            except:
                pass

            # Count for like(s)/view(s)
            try:
                popularity_count = element.find_element_by_css_selector("span > span").text
            except:
                popularity_count = len(element.find_elements_by_tag_name("a"))

            # Save like(s)/view(s) and video url
            try:
                post["video"] = self.driver.find_element_by_tag_name("video").get_attribute("src")
                post["views"] = popularity_count
                print("Video: {}".format(post["video"]))
                print("View(s): {}".format(popularity_count))
            except:
                post["likes"] = popularity_count
                print("Picture: {}".format(post["image"]))
                print("Like(s): {} ".format(popularity_count))

            print()

        end_dt = datetime.datetime.now()
        time_diff = end_dt - start_dt
        print("Total: {} post(s)".format(len(posts)))
        print("Total: {} error(s)".format(errors))
        print("Total: {} second(s)".format(time_diff.seconds))
        return posts


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Instagram Scrapper")
    parser.add_argument('hashtag', help="Hashtag to search")
    parser.add_argument('--maxpage', default=10, help="Maximum page to scroll (Default: 10)")
    parser.add_argument('--maxpost', default=1000, help="Maximum post to get (Defaut: 1000)")
    args = parser.parse_args()

    with Scrapstagram() as scrapper:
        scrapper.get_post_by_hashtag(args.hashtag, max_page=args.maxpage, max_post=args.maxpost)
