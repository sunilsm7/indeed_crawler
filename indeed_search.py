import csv
import logging
import pandas as pd
import re
import os

from datetime import datetime, date

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException


from bs4 import BeautifulSoup
import urllib.request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

scope = [
    "https://spreadsheets.google.com/feeds",
    'https://www.googleapis.com/auth/spreadsheets',
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]


BASE_URL = 'https://www.indeed.co.uk/advanced_search?q={}&l={}&radius=50'
CSV_URL = ''


class IndeedCrawlerException(Exception):
    pass


class IndeedCrawler:
    """
    Crawler to get jobs results from indeed.
    """

    def __init__(self):
        self.base_url = BASE_URL
        self.csv_url = CSV_URL
        self.results = []
        self.keywords = []
        self.sheet_id = "1d7hS1n4mLsgXK722aDfiXx1H7x38Ih8VwnPuV_ku7uM"
        self.driver = None
        self.current_date = str(date.today())
        self.service_account_path = "D:\\projects\\web-crawlers\\craigslist\\credentials.json"
        self.delay= 10
        self.creds = Credentials.from_service_account_file(self.service_account_path, scopes=scope)
        self.gc_client = gspread.authorize(self.creds)

    def read_sheets_keywords(self):
        """
        read keywords from google sheet file
        """
        sheet = self.gc_client.open_by_key(self.sheet_id)
        worksheet = sheet.worksheet('KeywordsIndeed')
        self.keywords = worksheet.get_all_records()
        return self.keywords

    def update_google_spread_sheet(self, results):
        """
        update extracted results to google sheet
        """
        if results:
            sheet = self.gc_client.open_by_key(self.sheet_id)
            worksheet = sheet.worksheet('Indeed')
            worksheet.append_rows(results)

    def crawl(self):
        crawl_keywords = self.read_sheets_keywords()

        for item in crawl_keywords: 
            keyword = item.get('Keyword')
            location = item.get('Location')
            domain = item.get('Domain')

            self.crawl_keyword(keyword, location)

    def crawl_keyword(self, search_query, location_query):
        results = []

        # instantiate a chrome options object so you can set the size and headless preference
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")

        url = self.base_url.format(search_query, location_query)
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        try:
            # wait = WebDriverWait(driver, self.delay)
            # wait.until(EC.presence_of_element_located((By.ID, 'searchform')))
            # logger.info('Page is ready')

            # modify search
            search_form = driver.find_element_by_name('sf')
            query = driver.find_element_by_name('as_and')
            location = driver.find_element_by_id('where')
            results_limit = driver.find_element_by_id('limit')
            sort_by = driver.find_element_by_id('sort')
            norecruiters = driver.find_element_by_id('norecruiters').click()
            fromage = driver.find_element_by_id('fromage')
            results_limit.send_keys(50)
            sort_by.send_keys('date')
            fromage.send_keys('7')
            search_form.submit()

            links = driver.find_elements_by_css_selector("div.jobsearch-SerpJobCard>h2.title>a")                                 

            for link in links:
                job_url = link.get_attribute('href')
                job_title = link.get_attribute('text')
                job_post = [self.current_date, search_query, location_query, job_title, '', job_url]
                results.append(job_post)

            logger.info('results:', results)
            # push results to google sheets
            # self.update_google_spread_sheet(results)

        except TimeoutException:
            logger.error('Loading took too much time')

        # close driver
        driver.close()
        return results


def main():
    indeed_crawler = IndeedCrawler()
    indeed_crawler.crawl()


if __name__ == '__main__':
    main()