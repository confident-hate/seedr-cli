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
from rich.table import Table
from datetime import datetime
from rich.console import Console

console = Console()

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
    'Accept-Encoding': 'gzip, deflate',
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
        console.print("Invalid input. Exiting...", style="red")


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
            console.print(f"Error: {out['result']}", style="red")
            console.print(
                f"[cyan]{out['wt']['title']}[/cyan] is added to wishlist.")
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
            name = JSONSTATS['folders'][item]['name']
            size = str(
                round(int(JSONSTATS['folders'][item]['size']) / 1024 / 1024, 2)
            ) + ' MB'
            folderID = JSONSTATS['folders'][item]['id']
            console.print(f'[bold cyan]📁{name} {size}[/bold cyan]')
            folderContent(folderID)
    else:
        console.print("\nEmpty list.", style="magenta")
    print("\nChecking wishlist items: ")
    if not getWishlistItemsList():
        console.print("Wishlist is empty.", style="magenta")


def utc2local(utc):
    epoch = time.mktime(utc.timetuple())
    offset = datetime.fromtimestamp(epoch) - datetime.utcfromtimestamp(epoch)
    return utc + offset


def time_ago(dt):
    DAY_INCREMENTS = [[365, "year"], [30, "month"], [7, "week"], [1, "day"], ]
    SECOND_INCREMENTS = [[3600, "hour"], [60, "minute"], [1, "second"], ]
    diff = datetime.now() - dt
    if diff.days < 0:
        return "in the future?!?"
    for increment, label in DAY_INCREMENTS:
        if diff.days >= increment:
            increment_diff = int(diff.days / increment)
            return str(increment_diff) + " " + label + plural(increment_diff) + " ago"
    for increment, label in SECOND_INCREMENTS:
        if diff.seconds >= increment:
            increment_diff = int(diff.seconds / increment)
            return str(increment_diff) + " " + label + plural(increment_diff) + " ago"
    return "just now"


def plural(num):
    if num != 1:
        return "s"
    return ""


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
        console.print("The list is empty. Exiting...", style="red")
        exit()
    folder_list_dict = {
        'torrents': []
    }
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("SN", style="dim")
    table.add_column("Torrent Name")
    table.add_column("Size", justify="center")
    table.add_column("Time", justify="center")
    for item in range(len(TorrList)):
        name = TorrList[item]['name'][:75]
        size = str(
            round(int(TorrList[item]['size']) / 1024 / 1024, 2)
        ) + ' MB'
        time = time_ago(utc2local(datetime.strptime(
            TorrList[item]['last_update'], '%Y-%m-%d %H:%M:%S')))
        table.add_row(str(item + 1), name, size, time)
        folderID = TorrList[item]['id']
        temp_dict = {
            'title': name,
            'size': size,
            'id': folderID
        }
        folder_list_dict['torrents'].append(temp_dict)
    console.print(table)

    while 1:
        try:
            input_from_user = input(
                "Torrent to delete: (eg: \"1,2,3\", \"1 2 3\", \"1-5\", \"ALL\")\n")
            if input_from_user.upper() == 'ALL':
                for i in range(len(folder_list_dict['torrents'])):
                    deleteTorrent(
                        str(folder_list_dict['torrents'][i]['id']))
                console.print(
                    "All torrents deleted successfully.", style="green")
                break
            intermediate = [int(input_from_user)]
        except KeyboardInterrupt:
            console.print("Exiting...", style="red")
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
                console.print("Invalid input. Try again...", style="red")
                continue
        for item in intermediate:
            if (item-1) >= 0 and (item-1) < len(folder_list_dict['torrents']):
                deleteTorrent(str(folder_list_dict['torrents'][item-1]['id']))
                console.print(
                    f"Deleted: [green]{folder_list_dict['torrents'][item-1]['title']} [/green]"
                    f"[cyan]{folder_list_dict['torrents'][item-1]['size']}[/cyan]")
            else:
                console.print("Invalid input.", style="red")
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
            console.print(f'[bold cyan]📁{name}[/bold cyan]')
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
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Torrent Name")
            table.add_column("Size", justify="center")
            table.add_row(active_torrent_name, active_torrent_size)
            console.print(table)
            user_input = input(
                "Do you want to delete this active torrent? y/n\n")
            if user_input.lower() == 'y':
                deleteActiveTorrent(active_torrent_id)
    else:
        console.print("No active torrents found.", style="green")


def activeTorrentProgress():
    activeTorrents = active_torrent_list()
    if len(activeTorrents) == 0:
        console.print(
            "All downloads finished! there are no active torrents.", style="green")
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
                        print(f'{" "*100 }', end='\r')
                        if progressPercentage == 101:
                            print(
                                f'{name} {size} {ddlRate} Q{quality} S{seeders} L{leechers} Finished')
                            return True
                        else:
                            bar, percents = progress(progressPercentage, 101)
                            console.print(
                                f'{name[:50]}[[green]{bar}[/green]] [magenta]{percents}% {size} {ddlRate} S{seeders}[/magenta]', end='\r')
                        time.sleep(2)

                except KeyError:
                    print('Collecting Seeds...', end='\r')
                    time.sleep(2)
                except KeyboardInterrupt:
                    console.print("\nExiting...", style="red")
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
            console.print(f'[cyan]  📓{filename} {size}[/cyan]')
            console.print(f'[green]    🔗{sharedURL}[/green]')
            # Clickable link
            # text = "LINK"
            # target = sharedURL
            # print(f'{filename} {size}',
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
        console.print("Error: There is not enough space.", style="red")
    if r.json()['result'] == 'queue_full_added_to_wishlist':
        console.print(
            "Error: There are some active downloads going.", style="red")


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
        if len(wishlist) < 1:
            console.print("The list is empty. Exiting...", style="magenta")
            exit()
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
                        console.print("Invalid Input.", style="red")
                except ValueError:
                    console.print("Invlid input", style="red")
                except KeyboardInterrupt:
                    console.print("Exiting...", style="red")
                    exit()
        else:
            console.print("Wishlist is empty. Exiting...", style="magenta")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\nExiting...", style="red")
        exit()
    exit()
