import sys
import requests
from bs4 import BeautifulSoup

user_agent = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36'
}


def getMegnet(url):
    response = requests.get(url, headers=user_agent)
    soup = BeautifulSoup(response.content, 'html.parser')
    magnetLink = soup.select('a[href^="magnet"]')[0]['href']
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
        seeds = soup.select('td.coll-2')
        leeches = soup.select('td.coll-3')
        size = soup.select('td.coll-4')
        uploader = soup.select('td.coll-5')

        torrents_dict = {
            'torrents': []
        }

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
