import os
import sys
import time
import pickle
import requests
import pytesseract
from PIL import Image
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = Options()
options.add_argument('--no-sandbox')
options.add_argument("--headless")


home = os.path.expanduser('~')
user_agent = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/81.0'
}

FFprofile = webdriver.FirefoxProfile()
FFprofile.set_preference('network.http.spdy.enabled.http2', False)
driver = webdriver.Firefox(options=options, firefox_profile=FFprofile)
se = requests.Session()


def CaptchaCheck():
    url = 'https://rarbgtorrents.org/torrents.php'

    if os.path.isfile(f'{home}/.config/seedr-cli/rarbg.cookie'):
        mycookie = pickle.load(
            open(f'{home}/.config/seedr-cli/rarbg.cookie', 'rb'))
        for cook in mycookie:
            se.cookies.set(cook['name'], cook['value'])
    response = se.post(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    if "verify your browser" in soup.text:
        print("Captcha found.")
        return True


def img2txt():
    try:
        clk_here_button = driver.find_element_by_link_text('Click here')
        clk_here_button.click()
        time.sleep(10)
    except:
        pass

    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'solve_string'))
        )
    finally:
        element = driver.find_elements_by_css_selector('img')[1]
        location = element.location
        size = element.size
        driver.save_screenshot(f"{home}/.config/seedr-cli/image.png")
        x = location['x']
        y = location['y']
        width = location['x']+size['width']
        height = location['y']+size['height']
        im = Image.open(f"{home}/.config/seedr-cli/image.png")
        im = im.crop((int(x), int(y), int(width), int(height)))
        im.save(f"{home}/.config/seedr-cli/final.png")
        return pytesseract.image_to_string(Image.open(f"{home}/.config/seedr-cli/final.png"))


def solveCaptcha():
    driver.implicitly_wait(10)
    driver.get('https://rarbgtorrents.org/torrents.php')
    solution = img2txt()
    # print(solution)

    text_field = driver.find_element_by_id('solve_string')
    text_field.send_keys(solution)
    text_field.send_keys(Keys.RETURN)
    time.sleep(3)
    selCookie = driver.get_cookies()
    pickle.dump(selCookie, open(
        f'{home}/.config/seedr-cli/rarbg.cookie', 'wb'))


def search(somestring):
    url = f'https://rarbgtorrents.org/torrents.php?search={somestring}&order=seeders&by=DESC'
    response = se.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    torrents_dict = {
        'torrents': []
    }
    try:
        lista2 = soup.select('.lista2')
        if len(lista2) == 0:
            print("No search result found. Exiting...")
            sys.exit()
        print("SN".ljust(4), "TORRENT NAME".ljust(80), "SEEDS".ljust(6),
              "LEECHES".ljust(6), "SIZE".center(12), "UPLOADER")
        for i in range(10):
            torrent_name = lista2[i].contents[1].contents[0].contents[0][:75]
            torrent_size = lista2[i].contents[3].contents[0]
            torrent_seeds = lista2[i].contents[4].contents[0].contents[0]
            torrent_leeches = lista2[i].contents[5].contents[0]
            torrent_uploader = lista2[0].contents[7].contents[0]
            print(str(i + 1).ljust(4), torrent_name.ljust(80), torrent_seeds.ljust(6),
                  torrent_leeches.ljust(6), torrent_size.center(12), torrent_uploader)
            href_link = f'https://rarbgtorrents.org{lista2[i].contents[1].contents[0]["href"]}'
            temp_dict = {
                'name': torrent_name,
                'size': torrent_size,
                'seeds': torrent_seeds,
                'leeches': torrent_leeches,
                'uploader': torrent_uploader,
                'href': href_link
            }
            torrents_dict['torrents'].append(temp_dict)
    except IndexError:
        pass
    while 1:
        try:
            input_index = int(input("Select torrent to add...\n")) - 1
            if input_index >= 0 and input_index < len(torrents_dict['torrents']):
                goto_link = torrents_dict['torrents'][input_index]['href']
                return getMegnet(goto_link)
            else:
                print("Invalid input")
        except ValueError:
            print("Invlid input")
        except KeyboardInterrupt:
            print("\nExiting...")
            sys.exit(0)


def getMegnet(url):
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    magnetLink = soup.select('a[href^="magnet"]')[0]['href']
    # print(magnetLink)
    return magnetLink


def initial(TEXT):
    count = 0
    while CaptchaCheck():
        count += 1
        print(f"Solving Captcha...try {count}")
        solveCaptcha()
    driver.close()
    return search(TEXT)
