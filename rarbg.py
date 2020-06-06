import requests
from bs4 import BeautifulSoup
import sys
import os
from selenium import webdriver
import time


if os.path.isfile('rarbgcookie.txt'):
    with open('rarbgcookie.txt', 'r') as f:
        myrarbgcookie = f.read()
else:
    myrarbgcookie = ''

user_agent = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
    'cookie': myrarbgcookie
}


def CaptchaCheck():
    global myrarbgcookie
    url = 'https://rarbgtorrents.org/torrents.php'

    response = requests.post(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    if "verify your browser" in soup.text:
        print("Captcha found.")
        return True
    else:
        return False


def solveCaptcha():
    driver = webdriver.Firefox()
    driver.get("https://rarbgtorrents.org/torrents.php")
    initial_cookies = driver.get_cookies()
    while 1:
        time.sleep(2)
        if initial_cookies != driver.get_cookies():
            print("CAPTCHA Solved!")
            final_cookies = driver.get_cookies()
            # print(final_cookies)
            dest = ''
            for item in final_cookies:
                name = item['name']
                value = item['value']
                dest += f'{name}={value};'
            driver.close()
            return dest[:-1]


def search(somestring):
    url = f'https://rarbgtorrents.org/torrents.php?search={somestring}'
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    href_list = []
    try:
        print("SN".ljust(4), "TORRENT NAME".ljust(80), "SEEDS".ljust(6),
              "LEECHES".ljust(6), "SIZE".center(12), "UPLOADER")
        lista2 = soup.select('.lista2')
        for i in range(10):
            torrent_name = lista2[i].contents[1].contents[0].contents[0][:75]
            torrent_size = lista2[i].contents[3].contents[0]
            torrent_seeds = lista2[i].contents[4].contents[0].contents[0]
            torrent_leeches = lista2[i].contents[5].contents[0]
            torrent_uploader = lista2[0].contents[7].contents[0]
            print(str(i + 1).ljust(4), torrent_name.ljust(80), torrent_seeds.ljust(6),
                  torrent_leeches.ljust(6), torrent_size.center(12), torrent_uploader)
            href_link = f'https://rarbgtorrents.org{lista2[i].contents[1].contents[0]["href"]}'
            href_list.append(href_link)
    except IndexError:
        pass
    while 1:
        try:
            input_index = int(input("Select torrent to add...\n")) - 1
            if input_index > 0 and input_index < len(href_list):
                goto_link = href_list[input_index]
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
    global user_agent
    if CaptchaCheck():
        myrarbgcookie = solveCaptcha()
        with open('rarbgcookie.txt', 'w') as f:
            f.write(myrarbgcookie)
        user_agent = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
            'cookie': myrarbgcookie
        }
    return search(TEXT)
