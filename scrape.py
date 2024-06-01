#Data libraries
import re
import csv
import requests
import pandas as pd
import numpy as np

#Scraping
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


film_rating_list = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'X', 'GP', 'M', 'M/PG']

# Create browser obj
service = Service(executable_path='chromedriver/chromedriver')
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=service, options=options)

with open('output/mpaa_db.csv', 'w') as file:
    csv_writer = csv.writer(file)

    for film_year in range(1990, 2025): #1968

        for film_rating in film_rating_list:

            # Generate current url
            current_url = f'https://www.filmratings.com/Search?filmYear={film_year}&filmRating={film_rating}'

            #Request url
            driver.get(current_url)
            sleep(0.5)

            # Fetch source HTML
            html = driver.page_source
            webpage = BeautifulSoup(html,'html.parser')

            has_next_page = True
            while has_next_page:

                html = driver.page_source
                webpage = BeautifulSoup(html,'html.parser')

                movies_list = (webpage.find_all('div', attrs={'class':'resultRow'}))

                for m in movies_list:
                    print("\n")

                    film_title = m.find('div', attrs={'class':'resultData _filmTitle topRow'}).string # [:-7]
                    print("Film Title: " + film_title)

                    cert_number = m.find_all('div', attrs={'class':'resultData'})[2].string
                    if cert_number is None:
                        cert_number = "NA"
                    print("Cert Number: " + cert_number)

                    rating_descriptors = m.find_all('div', attrs={'class':'resultData'})[3].string.strip()
                    print("Descriptors: " + rating_descriptors)

                    distributor = m.find_all('div', attrs={'class':'resultData'})[4].string
                    if distributor is None:
                        distributor = "NA"
                    print("Distributor: " + distributor)

                    alternate_titles = m.find_all('div', attrs={'class':'resultData'})[5].string.strip()
                    print("Alternate Titles: " + alternate_titles)

                    other_notes = m.find_all('div', attrs={'class':'resultData'})[6].string.strip()
                    print("Other Notes: " + other_notes)
                
                    # Write data for the current film to the output CSV file
                    csv_writer.writerow([cert_number, film_title, str(film_year), film_rating, rating_descriptors, alternate_titles, other_notes])
                
                if len(webpage.find_all('a', attrs={'class':'next'})) > 0:
                    next_button = driver.find_element(By.CLASS_NAME, "next")

                    if next_button.get_attribute("href"):
                        next_button.click()
                        sleep(0.5) 
                    else:
                        has_next_page = False
                else:
                    has_next_page = False