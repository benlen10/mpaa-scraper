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

with open('mpaa_db.csv', 'w') as file:
    csv_writer = csv.writer(file)

    for film_year in range(1968, 2024):

        for film_rating in film_rating_list:

            # Generate current url
            current_url = f'https://www.filmratings.com/Search?filmYear={film_year}&filmRating={film_rating}'

            #request url
            driver.get(current_url)
            sleep(1) 

            html = driver.page_source
            webpage = BeautifulSoup(html,'html.parser')

            has_next_page = True
            while has_next_page:

                html = driver.page_source
                webpage = BeautifulSoup(html,'html.parser')

                movies_list = (webpage.find_all('div', attrs={'class':'resultRow'}))

                for m in movies_list:
                    print("\n")

                    film_title = m.find('div', attrs={'class':'resultData _filmTitle topRow'}).string
                    print("Film Title: " + film_title)

                    # film_rating = m.find('div', attrs={'class':'resultData _filmRating'}).string
                    # print("Film Rating: " + film_rating)

                    cert_number = m.find_all('div', attrs={'class':'resultData'})[2].string
                    
                    if cert_number is None:
                        cert_number = "NA"
                    print("Cert Number: " + cert_number)

                    rating_descriptors = m.find_all('div', attrs={'class':'resultData'})[3].string
                    print("Descriptors: " + rating_descriptors)

                    other_notes = m.find_all('div', attrs={'class':'resultData'})[5].string
                    print("Other Notes: " + other_notes)
                
                    csv_writer.writerow([cert_number, film_title, str(film_year), film_rating, rating_descriptors, other_notes])
                
                if len(webpage.find_all('a', attrs={'class':'next'})) > 0:
                    next_button = driver.find_element(By.CLASS_NAME, "next")

                    if next_button.get_attribute("href"):
                        next_button.click()
                        sleep(1) 
                    else:
                        has_next_page = False
                else:
                    has_next_page = False