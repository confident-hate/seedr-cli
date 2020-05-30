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
usage: main.py [-h] [-s] [-a ADD] [-S SEARCH] [-d]

optional arguments:
  -h, --help                                             show this help message and exit
  -s, --stats                                            display full stats of seedr account
  -a ADD, --add ADD                            add a magnet link or a torrent file path from disk
  -S SEARCH, --search SEARCH          find a torrent on 1337x.to
  -d, --delete                                         delete a torrent
  
 ```
