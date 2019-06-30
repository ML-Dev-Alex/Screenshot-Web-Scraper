from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
import time
import requests
import re
import os
import tldextract
import random

def screenshotScrape(sites, strings, unwanted_ids, delayed_ids, save_folder, max_pages=50):
    """
    Screnshoots(in multiple resolutions and zoom levels) all sites on the list provided by the user,
    then follows links in those sites to sites that contain at least one of the
    user defined strings on its url and screenshots it too. Keeps going recursively untill it reaches the max
    number of pages defined by the user (50 by default).
    :param sites: List of pages to be scraped.
    :param strings: List of words to look for on the urls in order to only follow relevant links.
    :param unwanted_ids: List of element ids to be clicked in order to clear it from the screen.
    :param delayed_ids: List of element ids, that appear after scrolling a little, 
    to be clicked in order to clear it from the screen.
    :param save_folder: String to location that will store saved screenshots.
    :param max_pages: Maximum number of links to follow from the list of sites.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--test-type')
    options.add_argument(f'--proxy-server={None}')
    options.binary_location = '/usr/bin/chromium'
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # Full list of most common resolutions
    # resolutions = [
    # # 4:3
    # (640, 480), (800, 600), (960, 720), (1024, 768), (1280, 960), (1400, 1050),
    # (1440, 1080), (1600, 1200), (1856, 1392), (1920, 1440), (2048, 1536),
    # # 16:10
    # (1280,800), (1440, 900), (1680, 1050), (1920, 1200), (2560, 1600),
    # # 16:9
    # (1024, 576), (1152, 648), (1280, 720), (1366, 768), (1600, 900), (1920, 1080),
    # (2560, 1440), (3840, 2160), (7680, 4320)
    # ]


    resolutions = [
        # 4:3
        (640, 480), 
        # 16:10
        (1280,800),
        # 16:9
        (1920, 1080), 
        # 9:16 - Vertical (mobile) 
        (768, 1336), 
        ]
    
    main_name = strings[0]

    # Create folder to store screenshots if it does not exist already
    if not os.path.isdir(f'{save_folder}/{main_name}'):
        print(f'Created folder at {save_folder}/{main_name}')
        os.makedirs(f'{save_folder}/{main_name}')
    

    # While there are still sites to scrape, keep looking for more sites and taking screenshots
    for i in range(max_pages):
        current_site = sites[i]
        try:
            html_page = requests.get(current_site)
        except:
            continue
        soup = bs(html_page.text, 'lxml')
        links = []

        # Find all links on the current site and append them to a list
        for tag in soup.findAll('a'):
            current_link = tag.get('href')
            if current_link is not None:
                # If the link sends us to a full page append the whole string to the list
                if re.search('^http://', current_link) or re.search('^https://', current_link):
                    links.append(current_link)
                else:
                    # If the link is to a subdirectory add it to the end of the original site url
                    if current_link.startswith('/'):
                        links.append(f'{current_site}{current_link}')
                    # If it starts with a # it is usually just a menu item
                    elif current_link.startswith('#'):
                        pass
                    else:
                        links.append(f'{current_site}/{current_link}')

        # Remove duplicates from the list of links on the current page 
        links = list(dict.fromkeys(links))

        # Find all the links that point to sites with the desired strings on their titles
        # check if they have been already added to the list of sites to be scraped, and add them if not.
        for link in links:
            for word in strings:
                if word in link and link not in sites:
                    sites.append(link)    

        # After looking through the links on the current site its time to take the screenshots
        driver.set_page_load_timeout(30)
        driver.set_script_timeout(30)
        try:
            driver.get(current_site)
        except:
            continue
        
        # Try to close unwanted elements
        driver.implicitly_wait(5)
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        
        try:
            if unwanted_ids is not None:
                for id in unwanted_ids:
                    element = driver.find_element(by=By.ID, value=id)
            
            driver.execute_script("arguments[0].click();", element)
        except NoSuchElementException:
            pass
    
        # resolution variations
        for resolution in resolutions:
            current_width = resolution[0] + random.randrange(0, 100, 1)
            current_height = resolution[1] + random.randrange(0, 100, 1)
            driver.set_window_size(current_width, current_height)
            # j = zoom variations 
            for j in range(4):
                driver.implicitly_wait(1)
                driver.execute_script(f"document.body.style.zoom='{50 + j*50 + random.randrange(0, 25, 1)}%'")
                driver.execute_script('window.scrollTo(0, 0);')
                
                driver.save_screenshot(os.path.abspath(f'{save_folder}/{main_name}/1.png'))                
                
                window_width = driver.execute_script('return document.documentElement.scrollWidth;')
                
                last_y = 0
                current_y = 0
                # k = scroll variations 
                for k in range(200):
                    # Close delayed elements
                    if k == 5:
                        try:
                            if delayed_ids is not None:
                                for id in delayed_ids:
                                    element = driver.find_element(by=By.ID, value=id)
                            driver.execute_script("arguments[0].click();", element)
                        except NoSuchElementException:
                            pass
                        
                    current_y = driver.execute_script('return window.pageYOffset;')
                    
                    # If we have reached the end of the page break early
                    # Otherwise keep scrolling and taking more screenshots
                    if current_y == last_y and k != 0:
                        break
                    driver.execute_script(f'window.scrollTo({random.randrange(0, window_width, 1)}, {(200 + (j*100) + random.randrange(1, 25, 1))*(k+1)});')
                    number = len(os.listdir(os.path.abspath(f'{save_folder}/{main_name}')))
                    driver.save_screenshot(os.path.abspath(f'{save_folder}/{main_name}/{number + 1}.png'))
                    
                    last_y = current_y
                        
    driver.close()


if __name__ == "__main__":
    save_folder = os.path.abspath('/media/alexandre/Data/ScreenShots')
    
    sites = ['https://www.examplesite.com.br/', 'http://www.otherexample.com/']
    
    strings = ['domain_name', 'name', 'domainName']
    
    ids = ['close_prompt', 'close_login']
    
    delayed_ids = ['expanding_cta_close_button', 'close_button_login']
    
    screenshotScrape(sites, strings, ids, delayed_ids, save_folder)
