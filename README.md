# seedr-cli 
A tool to ease tasks on seedr.cc
## Table of Contents
  * [Installation](#installation)
  * [Features](#features)
  * [Usage](#usage)


## Installation

First install firefox web browser on your machine.

**For LINUX:**

```bash
$ git clone https://github.com/confident-hate/seedr-cli.git
$ cd seedr-cli
$ pip install -r requirements.txt
$ sudo bash install.sh --install
```
To uninstall seedr, execute the command `seedr --uninstall`

**For Windows:**

Install [tesseract-ocr](https://github.com/UB-Mannheim/tesseract/wiki) for rarbg usage(optional). And make sure python, geckodriver and tesseract are in environment variable PATH.

```powershell
PS D:\> git clone https://github.com/confident-hate/seedr-cli.git
PS D:\> cd .\seedr-cli\
PS D:\seedr-cli> pip install -r requirements.txt
PS D:\seedr-cli> python .\main.py -h
```

## Features
  * Add/Delete torrents 
  * Support for both magnet link and torrent file
  * Full stats in tree like structure (upto 1 level deep)
  * Search torrents via 1337x.to
  * Search torrents via RARBG
  
## Usage

```
$ seedr -h
usage: main.py [-h] [-s] [-a ADD] [-S SEARCH] [-Sr RARBG] [-d] [-w]

optional arguments:
  -h, --help  
                     show this help message and exit
  -A, --active
                     display active download progress
  -Ad, --activeDelete
                     delete active torrent
  -s, --stats                                           
                    display full stats of seedr account
  -a ADD, --add ADD                            
                    add a magnet link or a torrent file path from disk
  -S SEARCH, --search SEARCH          
                    find a torrent on 1337x.to
  -Sr RARBG, --rarbg RARBG, -SR RARBG
                    find a torrent on rarbg.to
  -d, --delete 
                    delete a torrent
  -w, --wishlist
                    list items from the wishlist
  
 ```
 First you need to login your account. Run this command:
 ```
 $ seedr
 ```
 
Add a torrent like this:
 ```
 $ seedr -a "magnet_link_goes_here"
 $ seedr -a "/path/to/torrent/file.torrent"
 200 OK
 Added:  <REDACTED>
 <REDACTED>[######                    ] 40% 2382.81MB 3.81MB/s S962
 ```
 
Delete a torrent like this:
 ```
 $ seedr -d
 200 OK
SN   TORRENT NAME                                                                         SIZE    
1    <File Name REDACTED>                                                              1018.27 MB 
Torrent to delete: (eg: "1,2,3", "1 2 3", "1-5", "ALL", "all")
 ```

To search torrents on 1337x.to, run this:
```
$ seedr -S "string to be searched"
```

To search torrents on RARBG.to, run this:
```
$ seedr --rarbg "string to be searched"
```

View entire account details with shareable links in tree like structure:
```
$ seedr -s
200 OK
USER                                        <REDACTED>
USER ID                                   <REDACTED>
MEMBERSHIP                         NON-PREMIUM
BANDWIDTH USED                40.23 TB
COUNTRY                                <REDACTED>
5.3 GB/8.0 GB used.
📁<Folder Name REDACTED> 1018.27 MB
  📓<File Name REDACTED> 1018.27 MB
    🔗https://fr.seedr.cc/ff_get/743824252/<REDACTED>

Checking wishlist items: 
Wishlist is empty
```

To list only shareble links use seedr with grep like this:
```
$ seedr -s | grep -o 'http.*'
https://fr.seedr.cc/ff_get/743824252/<REDACTED>
https://fr.seedr.cc/ff_get/743823522/<REDACTED>
https://fr.seedr.cc/ff_get/743826352/<REDACTED>
https://fr.seedr.cc/ff_get/743368252/<REDACTED>
```
You can even pipe it to clipboard manager like this:
```
$ seedr -s | grep -o 'http.*' | xsel -b
```

Play with wishlist items:
```
$ seedr -w
```
