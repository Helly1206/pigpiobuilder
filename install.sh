#!/bin/bash
NAME="pigpio_builder"
LNAME="pigpiobuilder"
OPTDIR="/opt"
OPTLOC="$OPTDIR/$NAME"
DEBFOLDER="debian"
BINNAME="/usr/bin/update_pigpio"

if [ "$EUID" -ne 0 ]
then
	echo "Please execute as root ('sudo install.sh' or 'sudo make install')"
	exit
fi

if [ "$1" == "-u" ] || [ "$1" == "-U" ]
then
	echo "$NAME uninstall script"

    echo "Removing files"
    unlink $BINNAME
	if [ -d "$OPTLOC" ]; then
        rm -rf "$OPTLOC"
    fi

elif [ "$1" == "-h" ] || [ "$1" == "-H" ]
then
	echo "Usage:"
	echo "  <no argument>: install $NAME"
	echo "  -u/ -U       : uninstall $NAME"
	echo "  -h/ -H       : this help file"
	echo "  -d/ -D       : build debian package"
	echo "  -c/ -C       : Cleanup compiled files in install folder"
elif [ "$1" == "-c" ] || [ "$1" == "-C" ]
then
	echo "$NAME Deleting compiled files in install folder"
	rm -f ./*.deb
	rm -rf "$DEBFOLDER"/$LNAME
	rm -rf "$DEBFOLDER"/.debhelper
	rm -f "$DEBFOLDER"/files
	rm -f "$DEBFOLDER"/files.new
	rm -f "$DEBFOLDER"/$LNAME.*
elif [ "$1" == "-d" ] || [ "$1" == "-D" ]
then
	echo "$NAME build debian package"
	fakeroot debian/rules clean binary
	mv ../*.deb .
else
	echo "$NAME install script"
	
    if [ ! -d "$OPTLOC" ]; then
        mkdir "$OPTLOC"
    fi
    cp -r ".$OPTLOC/." "$OPTLOC/"
    
    ln -s "$OPTLOC/$NAME.py" $BINNAME
fi
