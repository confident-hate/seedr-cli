#!/bin/bash

if [ "$(id -u)" != "0" ]; then
    echo "Run it as root"
	echo
	echo "usage: sudo bash install.sh --install | --uninstall"

else
	if [ "$1" = "--install" ] ; then
		if [ ! -f /usr/bin/geckodriver ] && [ ! -f /usr/local/bin/geckodriver ] ; then
			echo "[!] Downloading and Installing geckodriver"
			wget https://github.com/mozilla/geckodriver/releases/download/v0.28.0/geckodriver-v0.28.0-linux32.tar.gz -c -P /tmp/seedr-cli -q --show-progress || { echo "[-] Download failed ";exit 1;}
			tar -xf /tmp/seedr-cli/geckodriver-v0.28.0-linux32.tar.gz -C /usr/bin || exit 1
			chmod +x /usr/bin/geckodriver || exit 1
			echo "[+] geckodriver installed successfully"
		else
			echo "[+] geckodriver is already installed"
		fi

		if [ ! -d /usr/share/seedr-cli ]; then
			mkdir /usr/share/seedr-cli
		fi

		cp main.py rarbg.py mySelenium.py x1337.py install.sh /usr/share/seedr-cli || exit 1
		cp bin/seedr /usr/bin || exit 1
		chmod +x /usr/bin/seedr || exit 1
		echo "[+] Seedr installed successfully"

	elif [ "$1" = "--uninstall" ] ; then
		read -n1 -p "Would you like to remove the cookies too? y/[N]: " delCookies
		if [ $delCookies = "y" ] ; then
			USER_HOME=$(getent passwd $SUDO_USER | cut -d: -f6)
			rm -rf $USER_HOME/.config/seedr-cli
		fi
		echo
		if [ -d /usr/share/seedr-cli ] ; then
			rm -r  /usr/share/seedr-cli
		fi
		if [ -e /usr/bin/seedr ] ; then
			rm /usr/bin/seedr
		fi
		echo "[-_-] Seedr uninstalled successfully"
	else
		echo "usage: bash install.sh --install | --uninstall"
	fi			
fi 
