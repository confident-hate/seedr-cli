# seedr-cli 
A tool to ease tasks on seedr.cc
## Table of Contents
  * [Installation](#installation)
  * [Features](#features)
  * [Usage](#usage)


## Installation
Clone the repository
```bash
$ git clone https://github.com/confident-hate/seedr-cli.git
```

## Features
  * Add/Delete torrents 
  * Support for both magnet link and torrent file
  * Full stats in tree like structure (upto 1 level deep)
  * Search torrents via 1337x.to
  
## Usage

```
$ cd seedr-cli
$ python main.py -h
usage: main.py [-h] [-s] [-a ADD] [-S SEARCH] [-d] [-w]

optional arguments:
  -h, --help                                             show this help message and exit
  -s, --stats                                            display full stats of seedr account
  -a ADD, --add ADD                            add a magnet link or a torrent file path from disk
  -S SEARCH, --search SEARCH          find a torrent on 1337x.to
  -d, --delete                                         delete a torrent
  -w, --wishlist                                      List items from the wishlist
  
 ```
 First you need to login your account. Run this command:
 ```
 $ python main.py
 ```
 
Adding a torrent via this:
 ```
 $ python main.py -a "magnet_link_goes_here"
 $ python main.py -a "/path/to/torrent/file.torrent"
 ```
 
Delete a torrent:
 ```
 $ python main.py -d
 ```

To search torrents on 1337x.to, run this:
```
$ python main.py -S "string to be searched"
```

View entire account details with shareable links in tree like structure:
```
$ python main.py -s
```

Play with waitlist items:
```
$ python main.py -w
```