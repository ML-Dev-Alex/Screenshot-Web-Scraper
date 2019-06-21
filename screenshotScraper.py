from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
import time
import requests
import re
import os
import tldextract


def screenshotScrape(site, max_links_to_follow=100):
    """
    Scrapes screenshots from all pages on a domain.
    :param site: Starting page for the domain to be scraped.
    (Chose a page with many links to other pages in the same domain, like the 'site map' page,
    in order to be sure that the algorithm will reach every desired page). 
    :param max_links_to_follow: maximum number of links to follow on the same domain.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument("--test-type")
    options.binary_location = "/usr/bin/chromium"
    driver = webdriver.Chrome(ChromeDriverManager().install())

    resolutions = [
        # 4:3
        (640, 480), (800, 600), (960, 720), (1024, 768), (1280, 960), (1400, 1050), (1440, 1080), (1600, 1200), (1856, 1392), (1920, 1440), (2048, 1536),
        # 16:10
        (1280,800), (1440, 900), (1680, 1050), (1920, 1200), (2560, 1600),
        # 16:9
        (1024, 576), (1152, 648), (1280, 720), (1366, 768), (1600, 900), (1920, 1080), (2560, 1440), (3840, 2160), (7680, 4320)
        ]

    # Extract the domain name from the url and create a folder to store images
    # If one does not exist already
    site_domain = (tldextract.extract(site)).domain

    if not os.path.isdir(site_domain):
        os.makedirs(site_domain)
        
    # List of sites to scrape
    sites = [ site ]
    patience = 0

    # While there are still sites to scrape, keep looking for more sites in the domain and taking screenshots
    for i in range(max_links_to_follow):
        current_site = sites[i]
        html_page = requests.get(current_site)
        soup = bs(html_page.text, 'lxml')
        links = []

        # Find all links on the current site and append them to a list
        for tag in soup.findAll('a'):
            current_link = tag.get('href')
            # If the link sends us to a full page append the whole string to the list
            if re.search("^http://", current_link) or re.search("^https://", current_link):
                links.append(f"{current_link}")
            else:
                # If the link is to a subdirectory add it to the end of the original site url
                if current_link.startswith("/"):
                    links.append(f"{current_site}{current_link}")
                else:
                    links.append(f"{current_site}/{current_link}")

        # Remove duplicates from the list of links on the current page 
        links = list(dict.fromkeys(links))

        # Find all the links that point to sites on the same domain as the original site,
        # check if they have been already added to the list of sites to be scraped, and add them if not.
        for link in links:
            link_domain = (tldextract.extract(link)).domain
            # If we found a new link on the same domain, add it to the list
            if link_domain == site_domain and link not in sites:
                sites.append(link)


        # After looking through the links on the current site its time to take the screenshots
        driver.get(current_site)

        # resolution variations
        for resolution in resolutions:
            driver.set_window_size(resolution[0], resolution[1])
            # j = zoom variations (35 to 250, with stepsize 15)
            for j in range(7):
                driver.execute_script(f"document.body.style.zoom='{50 + j*25}%'")
                driver.execute_script("window.scrollTo(0, 0);")
                driver.save_screenshot(f"{site_domain}/{1}.png")
                last_pos = 0
                # k = scroll variations 
                for k in range(100):
                    # If we have reached the end of the page break early
                    current_y = driver.execute_script('return window.pageYOffset;')
                    if (current_y == last_pos) and current_y != 0:
                        break
                    else:
                        last_pos = current_y
                    
                    # Otherwise keep scrolling and taking more screenshots
                    driver.execute_script(f"window.scrollTo(0, {200*(k+1)});")
                    # time.sleep(0.01)
                    driver.save_screenshot(f"{site_domain}/{len(os.listdir(site_domain))+1}.png")
    driver.close()


if __name__ == "__main__":
    sites_to_scrape = ['http://python.org']
    for site in sites_to_scrape:
        screenshotScrape(site)
