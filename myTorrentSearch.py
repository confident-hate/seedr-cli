import requests
from bs4 import BeautifulSoup
import sys

user_agent = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'
}


def getMegnet(url):
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    magnetLink = soup.select('a[href^="magnet"]')[0]['href']
    # print(magnetLink)
    return magnetLink


def search(somestring):
    url = f'https://1337x.to/srch?search={somestring}'
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    if "Attention Required!" in str(soup.select('head > title')):
        print("IP blocked! Try changing VPN. I can't solve captcha")
        sys.exit(0)
    else:
        torrent_list = soup.select('a[href*="/torrent/"]')
        seeds = soup.select('td.coll-2.seeds')
        leeches = soup.select('td.coll-3.leeches')
        size = soup.select('td.coll-4.size.mob-uploader')
        uploader = soup.select('td.coll-5.uploader')

        href_list = []

        try:
            print("SN".ljust(4), "TORRENT NAME".ljust(80), "SEEDS".ljust(6),
                  "LEECHES".ljust(6), "SIZE".center(12), "UPLOADER")
            for i in range(10):
                torrent_name = torrent_list[i].getText()[:75]
                torrent_seeds = seeds[i].getText()
                torrent_leeches = leeches[i].getText()
                torrent_size = size[i].contents[0]
                torrent_uploader = uploader[i].getText()
                print(str(i + 1).ljust(4), torrent_name.ljust(80), torrent_seeds.ljust(6),
                      torrent_leeches.ljust(6), torrent_size.center(12), torrent_uploader)
                href_link = "https://1337x.to" + torrent_list[i]['href']
                href_list.append(href_link)
        except IndexError:
            pass

        input_index = int(input("Select torrent to add...\n")) - 1
        goto_link = href_list[input_index]

        return getMegnet(goto_link)


