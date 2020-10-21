#!/usr/bin/env python3

import os
import sys
import json
import time
import x1337
import rarbg
import pickle
import base64
import hashlib
import argparse
import requests
import bencodepy
import mySelenium
from colorama import Fore, init, deinit, Style
init(autoreset=True)

parser = argparse.ArgumentParser(
    description='A little script for seedr.', epilog='Enjoy!')
parser.add_argument('-A', '--active', action='store_true',
                    help='display active download progress')
parser.add_argument('-Ad', '--activeDelete',
                    action='store_true', help='delete active torrent')
parser.add_argument('-s', '--stats', action='store_true',
                    help='display full stats of seedr account')
parser.add_argument('-a', '--add', type=str,
                    help='add a magnet link or a torrent file path from disk')
parser.add_argument('-S', '--search', type=str,
                    help='find a torrent on 1337x.to')
parser.add_argument('-Sr', '--rarbg', '-SR', type=str,
                    help='find a torrent on rarbg.to')
parser.add_argument('-d', '--delete', action='store_true',
                    help='delete a torrent')
parser.add_argument('-w', '--wishlist', action='store_true',
                    help='list items from the wishlist')

args = parser.parse_args()

s = requests.Session()
home = os.path.expanduser('~')
if not os.path.exists(f'{home}/.config/seedr-cli/'):
    os.makedirs(f'{home}/.config/seedr-cli/')
if os.path.isfile(f'{home}/.config/seedr-cli/seedr.cookie'):
    mycookie = pickle.load(
        open(f'{home}/.config/seedr-cli/seedr.cookie', 'rb'))
    for cook in mycookie:
        s.cookies.set(cook['name'], cook['value'])

headr = {
    'Host': 'www.seedr.cc',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest'
}


def magnetCheck(stringPassed):
    if "magnet:?xt=" in stringPassed[:11]:
        addTorrent(stringPassed)
    elif os.path.isfile(stringPassed) and stringPassed.endswith('.torrent'):
        metadata = bencodepy.decode_from_file(stringPassed)
        subj = metadata[b'info']
        hashcontents = bencodepy.encode(subj)
        digest = hashlib.sha1(hashcontents).digest()
        b32hash = base64.b32encode(digest).decode()
        convertedMagnet = 'magnet:?'\
            + 'xt=urn:btih:' + b32hash\
            + '&dn=' + metadata[b'info'][b'name'].decode()\
            + '&tr=' + metadata[b'announce'].decode()\
            + '&xl=' + str(metadata[b'info'][b'piece length'])
        addTorrent(convertedMagnet)
    elif stringPassed.startswith('http') and stringPassed.endswith('.torrent'):
        addTorrent(stringPassed)
    else:
        print(f"{Fore.RED}Invalid input. Exiting...")


def addTorrent(magnet):
    global torrent_title
    url = 'https://www.seedr.cc/actions.php'
    if magnet[:4] == 'http':
        DATA = {
            'torrent_url': magnet,
            'folder_id': '-1'
        }
    else:
        DATA = {
            'torrent_magnet': magnet,
            'folder_id': '-1'
        }

    PARAMS = {
        'action': 'add_torrent'
    }

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)
    try:
        torrent_title = r.json()['title']
        print('Added: ', torrent_title)
    except KeyError:
        out = r.json()
        if out['result'] == 'not_enough_space_added_to_wishlist' or out['result'] == 'queue_full_added_to_wishlist':
            print(f"{Fore.RED}Error: {out['result']}")
            print(
                f"{Fore.CYAN}{out['wt']['title']}{Style.RESET_ALL} is added to wishlist.")
            exit()
    if activeTorrentProgress():
        fetch_links_after_add()


def stats():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    PARAMS2 = {'action': 'get_settings'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)

    r2 = s.post(url, params=PARAMS2, data=DATA, headers=headr)
    settingsJSON = r2.json()
    userID = str(settingsJSON['account']['user_id'])
    isPremium = settingsJSON['account']['package_name']
    bandwidth_used = str(
        round(int(settingsJSON['account']['bandwidth_used']) / 1024 / 1024 / 1024 / 1024, 2)) + ' TB'
    email = settingsJSON['account']['email']
    country = settingsJSON['country']
    JSONSTATS = r.json()
    space_max = str(
        int(JSONSTATS['space_max']) / 1024 / 1024 / 1024) + ' GB'
    space_used = str(
        round(int(JSONSTATS['space_used']) / 1024 / 1024 / 1024, 2)) + ' GB'

    print("USER ".ljust(30)+email, "USER ID ".ljust(30)+userID, "MEMBERSHIP ".ljust(30)+isPremium,
          "BANDWIDTH USED ".ljust(30)+bandwidth_used, "COUNTRY ".ljust(30)+country, sep='\n')
    print(space_used + '/' + space_max + ' used.')
    list = JSONSTATS['folders']
    if len(list) > 0:
        for item in range(len(list)):
            print("root")
            print("│")
            name = JSONSTATS['folders'][item]['name']
            size = str(
                round(int(JSONSTATS['folders'][item]['size']) / 1024 / 1024, 2)
            ) + ' MB'
            folderID = JSONSTATS['folders'][item]['id']
            print(f'├──{Fore.CYAN}{Style.DIM}📁{name} {size}')
            folderContent(folderID)
    else:
        print(f"{Fore.MAGENTA}\nEmpty list.")
    print("\nChecking wishlist items: ")
    if not getWishlistItemsList():
        print(f"{Fore.MAGENTA}Wishlist is empty.")


def newDelete():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)
    TorrList = r.json()['folders']
    if len(TorrList) < 1:
        print(f"{Fore.RED}The list is empty. Exiting...")
        exit()
    folder_list_dict = {
        'torrents': []
    }
    print("SN".ljust(4), "TORRENT NAME".ljust(80), "SIZE".center(12))
    for item in range(len(TorrList)):
        name = TorrList[item]['name'][:75]
        size = str(
            round(int(TorrList[item]['size']) / 1024 / 1024, 2)
        ) + ' MB'
        print(str(item + 1).ljust(4), name.ljust(80), size.center(12))
        folderID = TorrList[item]['id']
        temp_dict = {
            'title': name,
            'size': size,
            'id': folderID
        }
        folder_list_dict['torrents'].append(temp_dict)

    while 1:
        try:
            input_from_user = input(
                "Torrent to delete: (eg: \"1,2,3\", \"1 2 3\", \"1-5\", \"ALL\")\n")
            if input_from_user.upper() == 'ALL':
                for i in range(len(folder_list_dict['torrents'])):
                    deleteTorrent(
                        str(folder_list_dict['torrents'][i]['id']))
                print(f"{Fore.GREEN}All torrents deleted successfully.")
                break
            intermediate = [int(input_from_user)]
        except KeyboardInterrupt:
            print(f"{Fore.RED}Exiting...")
            exit()
        except ValueError:
            if "," in input_from_user:
                intermediate = [int(i) for i in input_from_user.split(',')]
            elif " " in input_from_user:
                intermediate = [int(i) for i in input_from_user.split(' ')]
            elif "-" in input_from_user:
                first, second = input_from_user.split('-')
                intermediate = [i for i in range(int(first), int(second)+1)]
            else:
                print(f"{Fore.RED}Invalid input. Try again...")
                continue
        for item in intermediate:
            if (item-1) >= 0 and (item-1) < len(folder_list_dict['torrents']):
                deleteTorrent(str(folder_list_dict['torrents'][item-1]['id']))
                print(
                    f"Deleted: {Fore.GREEN}{folder_list_dict['torrents'][item-1]['title']} "
                    f"{Fore.CYAN}{folder_list_dict['torrents'][item-1]['size']}")
            else:
                print(f"{Fore.RED}Invalid input.")
        break


def fetch_links_after_add():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    time.sleep(5)
    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    list = r.json()['folders']
    for item in list:
        name = item['name']
        if name[:50] == torrent_title[:50]:
            folderID = item['id']
            print(f'├──{Fore.CYAN}{Style.DIM}📁{name}')
            folderContent(folderID)


def progress(count, total):
    bar_len = 15
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '#' * filled_len + ' ' * (bar_len - filled_len)
    return bar, percents


def active_torrent_list():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    response = s.post(url, params=PARAMS, data=DATA, headers=headr)
    return response.json()['torrents']


def acive_torrrent_delete():
    activeTorrents = active_torrent_list()
    if len(activeTorrents) != 0:
        for i in range(len(activeTorrents)):
            active_torrent_id = activeTorrents[i]['id']
            active_torrent_name = activeTorrents[i]['name']
            active_torrent_size = str(
                round(int(activeTorrents[i]['size']) / 1024 / 1024, 2)) + ' MB'
            print(active_torrent_name,
                  active_torrent_size)
            user_input = input(
                "Do you want to delete this active torrent? y/n\n")
            if user_input.lower() == 'y':
                deleteActiveTorrent(active_torrent_id)
    else:
        print(f"{Fore.GREEN}No active torrents found.")


def activeTorrentProgress():
    activeTorrents = active_torrent_list()
    if len(activeTorrents) == 0:
        print(f"{Fore.GREEN}All downloads finished! there are no active torrents.")
        return True
    else:
        for i in range(len(activeTorrents)):
            progress_url = activeTorrents[i]['progress_url']
            progressPercentage = 0.0
            while progressPercentage < 100.0:
                try:
                    rr = requests.get(progress_url)
                    strJson = rr.text[2:-1]
                    d = json.loads(strJson)
                    if d['title']:
                        name = d['title'][:75]
                        size = str(
                            round(int(d['size']) / 1024 / 1024, 2)) + 'MB'
                        ddlRate = str(round(
                            int(d['stats']['download_rate']) / 1024 / 1024, 2)) + 'MB/s'
                        quality = d['stats']['torrent_quality']
                        # peers = d['connected_to']
                        seeders = d['stats']['seeders']
                        leechers = d['stats']['leechers']
                        progressPercentage = d['progress']
                        if progressPercentage == 101:
                            sys.stdout.write(
                                f'\r{name} {size} {ddlRate} Q{quality} S{seeders} L{leechers} Finished \n')
                            return True
                        else:
                            bar, percents = progress(progressPercentage, 101)
                            sys.stdout.write(
                                f'\r{name[:50]}[{Fore.GREEN}{bar}{Style.RESET_ALL}] {Fore.MAGENTA}{percents}% {size} {ddlRate} S{seeders}')
                            sys.stdout.flush()
                        time.sleep(2)

                except KeyError:
                    sys.stdout.write('\rCollecting Seeds...')
                    sys.stdout.flush()
                    time.sleep(2)
                except KeyboardInterrupt:
                    print(f"\n{Fore.RED}Exiting...")
                    exit()
                except:
                    pass


def folderContent(FID):
    DATA = {
        'content_type': 'folder',
        'content_id': FID
    }
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    newRequest = s.post(url, params=PARAMS, data=DATA, headers=headr)
    JSONSTATS = newRequest.json()
    filelist = JSONSTATS['files']
    for file in range(len(filelist)):
        filename = JSONSTATS['files'][file]['name']
        size = str(
            round(int(JSONSTATS['files'][file]['size']) / 1024 / 1024, 2)
        ) + ' MB'
        fileID = str(JSONSTATS['files'][file]['folder_file_id'])

        # only display stuff greater than 1 MB
        if (round(int(JSONSTATS['files'][file]['size']) / 1024 / 1024, 2)) > 1.0:
            sharedURL = fetchFileLink(fileID)
            print(f'│  ├──{Fore.CYAN}📓{filename} {size}',
                  f'│  │  {Fore.GREEN}└──🔗{sharedURL}', sep='\n')
            # Clickable link
            # text = "LINK"
            # target = sharedURL
            # print(f'│  ├──{filename} {size}',
            #       f"\u001b]8;;{target}\u001b\\{text}\u001b]8;;\u001b\\")


def fetchFileLink(fileid):
    url = 'https://www.seedr.cc/content.php'
    DATA = {
        'folder_file_id': fileid
    }
    PARAMS = {'action': 'fetch_file'}

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if (r.json()['result']) is True:
        return r.json()['url']
    else:
        return False


def removeItemfromWishlist(fileid):
    url = 'https://www.seedr.cc/actions.php'
    DATA = {
        'id': fileid
    }
    PARAMS = {'action': 'remove_wishlist'}

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if (r.json()['result']) is True:
        print("File is removed from wishlist.")


def DownloadTorrentFromWishlist(fileid):
    url = 'https://www.seedr.cc/actions.php'
    DATA = {
        'wishlist_id': fileid
    }
    PARAMS = {'action': 'add_torrent'}

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.json()['result'] is True:
        print("Torrent is added from wishlist")
        activeTorrentProgress()
    if r.json()['result'] == 'not_enough_space_added_to_wishlist':
        print(f"{Fore.RED}Error: There is not enough space.")
    if r.json()['result'] == 'queue_full_added_to_wishlist':
        print(f"{Fore.RED}Error: There are some active downloads going.")


def getWishlistItemsList():
    global wishlist_dict
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'get_settings'}
    DATA = {
        'lol': 'haha'  # I am not sure why requests is not working without data=
    }
    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.json()['result'] is True:
        wishlist = r.json()['account']['wishlist']
        wishlist_dict = {
            'wishlist_torrents': []
        }
        for item in range(len(wishlist)):
            item_title = wishlist[item]['title']
            item_id = wishlist[item]['id']
            print(str(item + 1).ljust(4), item_title)
            temp_dict = {
                'title': item_title,
                'id': item_id
            }
            wishlist_dict['wishlist_torrents'].append(temp_dict)
            return True
    else:
        return False


def deleteTorrent(folderid):
    url = 'https://www.seedr.cc/actions.php'
    PARAMS = {'action': 'delete'}
    DATA = {
        'delete_arr': f'[{{"type":"folder","id":"{folderid}"}}]'
    }
    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.status_code == 200:
        return True
    else:
        return False


def deleteActiveTorrent(user_torrent_id):
    url = 'https://www.seedr.cc/actions.php'
    PARAMS = {'action': 'delete'}
    DATA = {
        'delete_arr': f'[{{"type":"torrent","id":"{user_torrent_id}"}}]'
    }
    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.status_code == 200:
        return True
    else:
        return False


def loginCheck():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }

    r = s.post(url, params=PARAMS, data=DATA, headers=headr)
    try:
        if r.json()['result'] == 'login_required':
            returned_cookie = mySelenium.call_me_niggas()
            pickle.dump(returned_cookie, open(
                f'{home}/.config/seedr-cli/seedr.cookie', "wb"))
            print("Cookie added")
    except KeyError:
        pass
    except KeyboardInterrupt:
        print("Exiting...")
        exit()
    except:
        print("Unknown error...")
        exit()


def exit():
    deinit()
    sys.exit()


def main():
    loginCheck()
    if args.active:
        activeTorrentProgress()
    if args.activeDelete:
        acive_torrrent_delete()
    if args.stats:
        stats()
    if args.add:
        magnetCheck(args.add)
    if args.search:
        magnetCheck(x1337.search(args.search))
    if args.rarbg:
        magnetCheck(rarbg.initial(args.rarbg))
    if args.delete:
        newDelete()
    if args.wishlist:
        if getWishlistItemsList():
            while 1:
                try:
                    user_input = int(
                        input("Press 1) to delete, 2) to download, 3) to quit\n"))
                    if user_input == 1:
                        # code for deletion
                        wishlist_index = int(
                            input("Enter index to delete\n")) - 1
                        removeItemfromWishlist(
                            wishlist_dict['wishlist_torrents'][wishlist_index]['id'])
                    elif user_input == 2:
                        # code for download
                        global torrent_title
                        wishlist_index = int(
                            input("Enter index to download\n")) - 1
                        torrent_title = wishlist_dict['wishlist_torrents'][wishlist_index]['title']
                        DownloadTorrentFromWishlist(
                            wishlist_dict['wishlist_torrents'][wishlist_index]['id'])
                    elif user_input == 3:
                        exit()
                    else:
                        print(f"{Fore.RED}Invalid Input.")
                except ValueError:
                    print(f"{Fore.RED}Invlid input")
                except KeyboardInterrupt:
                    print(f"{Fore.RED}Exiting...")
                    exit()
        else:
            print(f"{Fore.MAGENTA}Wishlist is empty. Exiting...")


if __name__ == "__main__":
    main()
    exit()
