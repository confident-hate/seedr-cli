import requests
import sys
import os
import json
import time
import argparse
import bencodepy
import hashlib
import base64
import myTorrentSearch
import mySelenium

parser = argparse.ArgumentParser(
    description='A little script for seedr.', epilog='Enjoy!')
parser.add_argument('-s', '--stats', action='store_true',
                    help='display full stats of seedr account')
parser.add_argument('-a', '--add', type=str,
                    help='add a magnet link or a torrent file path from disk')
parser.add_argument('-S', '--search', type=str,
                    help='find a torrent on 1337x.to')
parser.add_argument('-d', '--delete', action='store_true',
                    help='delete a torrent')

args = parser.parse_args()
magnet = args.add
searchString = args.search

if os.path.isfile('cookie.txt'):
    with open('cookie.txt', 'r') as f:
        mycookie = f.read()
        # print(mycookie)
else:
    mycookie = ''
headr = {
    'Host': 'www.seedr.cc',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.seedr.cc/files',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Length': '66',
    'Origin': 'https://www.seedr.cc',
    'Connection': 'keep-alive',
    'Cookie': mycookie,
    'TE': 'Trailers'
}


def magnetCheck(stringPassed):
    if "magnet:?xt=" in stringPassed[:11]:
        #print("YAY its a magnet link")
        addTorrent(stringPassed)
    else:
        if os.path.isfile(stringPassed) and stringPassed.endswith('.torrent'):
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
            # print(convertedMagnet)
            addTorrent(convertedMagnet)


def addTorrent(magnet):
    global torrent_title
    url = 'https://www.seedr.cc/actions.php'
    DATA = {
        'torrent_magnet': magnet,
        'folder_id': '-1'
    }

    PARAMS = {
        'action': 'add_torrent'
    }

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)
    try:
        torrent_title = r.json()['title']
        print('Added: ', torrent_title)
    except KeyError:
        out = r.json()
        if out['result'] == 'not_enough_space_added_to_wishlist':
            print("Queue is full")
            print("Torrent Name:", out['wt']['title'], "(", round(
                int(out['wt']['size']) / 1024 / 1024, 2), "MB )")
            print("File id: ", out['wt']['id'], "is added to waitlist.")
            # print(out['wt'])
    activeTorrentProgress()


def stats():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    PARAMS2 = {'action': 'get_settings'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)

    r2 = requests.post(url, params=PARAMS2, data=DATA, headers=headr)
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
    print("root")
    print("│")
    list = JSONSTATS['folders']
    for item in range(len(list)):
        name = JSONSTATS['folders'][item]['name']
        size = str(
            round(int(JSONSTATS['folders'][item]['size']) / 1024 / 1024, 2)
        ) + ' MB'
        folderID = JSONSTATS['folders'][item]['id']
        print(f'├──{name} {size}')
        folderContent(folderID)


def newDelete():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    print(r.status_code, r.reason)
    TorrList = r.json()['folders']
    folder_id_list = []
    print("SN".ljust(4), "TORRENT NAME".ljust(80), "SIZE".center(12))
    for item in range(len(TorrList)):
        name = TorrList[item]['name'][:75]
        size = str(
            round(int(TorrList[item]['size']) / 1024 / 1024, 2)
        ) + ' MB'
        print(str(item + 1).ljust(4), name.ljust(80), size.center(12))
        folderID = TorrList[item]['id']
        folder_id_list.append(folderID)
    input_index = int(input("Select torrent to delete...\n")) - 1
    delete_this_id = str(folder_id_list[input_index])
    if deleteTorrent(delete_this_id):
        print("Deleted")
    else:
        print("Something went wrong")


def fetch_links_after_add():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    list = r.json()['folders']
    for item in list:
        name = item['name']
        if name == torrent_title:
            folderID = item['id']
            print(f'├──{name}')
            folderContent(folderID)


def activeTorrentProgress():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }
    r2 = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    # print(r2.json())
    if len(r2.json()['torrents']) == 0:
        print("All downloads finished! there are no active torrents.")
        fetch_links_after_add()
    else:
        activeTorrents = r2.json()['torrents']
        for i in range(len(activeTorrents)):
            progress_url = activeTorrents[i]['progress_url']
            progressPercentage = 0.0
            while progressPercentage < 100.0:
                rr = requests.get(progress_url)
                strJson = rr.text[2:-1]
                d = json.loads(strJson)
                # print(d)
                try:
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
                            sys.stdout.write('\r{0} {1} {2} Q{3} S{4} L{5} Finished \n'.format(
                                name, size, ddlRate, quality, seeders, leechers))
                            fetch_links_after_add()
                            sys.exit(0)
                        else:
                            sys.stdout.write('\r{0} {1} {2} Q{3} S{4} L{5} {6}% '.format(
                                name, size, ddlRate, quality, seeders, leechers, progressPercentage))
                            sys.stdout.flush()
                        time.sleep(2)

                except KeyError:
                    sys.stdout.write('\rCollecting Seeds...')
                    sys.stdout.flush()
                    time.sleep(2)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    sys.exit(0)


def folderContent(FID):
    DATA = {
        'content_type': 'folder',
        'content_id': FID
    }
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    newRequest = requests.post(
        url, params=PARAMS, data=DATA, headers=headr)
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
            # Clickable link
            text = "LINK"
            target = sharedURL
            print(f'│  ├──{filename} {size}',
                  f"\u001b]8;;{target}\u001b\\{text}\u001b]8;;\u001b\\")


def fetchFileLink(fileid):
    url = 'https://www.seedr.cc/content.php'
    DATA = {
        'folder_file_id': fileid
    }
    PARAMS = {'action': 'fetch_file'}

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    if (r.json()['result']) is True:
        return r.json()['url']
    else:
        return False


def removeItemfromWaitlist(fileid):
    url = 'https://www.seedr.cc/actions.php'
    DATA = {
        'id': fileid
    }
    PARAMS = {'action': 'remove_wishlist'}

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    if (r.json()['result']) is True:
        print("File is removed from waitlist.")


def DownloadTorrentFromWishlist(fileid):
    url = 'https://www.seedr.cc/actions.php'
    DATA = {
        'wishlist_id': fileid
    }
    PARAMS = {'action': 'add_torrent'}

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.json()['result'] is True:
        print("Torrent is added from waitlist")


def getWishlistItemsList():
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'get_settings'}
    DATA = {
        'lol': 'haha'  # I am not sure why requests is not working without data=
    }
    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    if r.json()['result'] is True:
        wishlist = r.json()['account']['wishlist']
        for item in range(len(wishlist)):
            print(item + 1, ':', wishlist[item]['title'],
                  "with id", wishlist[item]['id'])


def deleteTorrent(folderid):
    url = 'https://www.seedr.cc/actions.php'
    PARAMS = {'action': 'delete'}
    DATA = {
        'delete_arr': "[{\"type\":\"folder\",\"id\":\""+folderid+"\"}]"
    }
    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    # print(r.url)
    # print(r.json())
    if r.status_code == 200:
        return True
    else:
        return False


def loginCheck():
    global mycookie
    url = 'https://www.seedr.cc/content.php'
    PARAMS = {'action': 'list_contents'}
    DATA = {
        'content_type': 'folder',
        'content_id': '0'
    }

    r = requests.post(url, params=PARAMS, data=DATA, headers=headr)
    try:
        if r.json()['result'] == 'login_required':
            #print("Let's grab new cookie via selelium :)")
            mycookie = mySelenium.call_me_niggas()
            with open('cookie.txt', 'w') as f:
                f.write(mycookie)
    except KeyError:
        pass
    except KeyboardInterrupt:
        print("Ctrl + c detected...")
        sys.exit(0)
    except:
        print("Unknown error...")
        sys.exit(0)


loginCheck()
if args.stats:
    stats()
if magnet:
    magnetCheck(magnet)
if searchString:
    magnetCheck(myTorrentSearch.search(searchString))
if args.delete:
    newDelete()
