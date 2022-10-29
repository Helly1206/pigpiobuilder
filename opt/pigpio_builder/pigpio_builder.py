#!/usr/bin/python3

# -*- coding: utf-8 -*-
#########################################################
# SCRIPT : pigpio_builder.py                            #
#          this script checks for a new version of      #
#          pigpio on github.                            #
#          If exists, it will be built and installed.   #
#          I. Helwegen 2020                             #
#########################################################

####################### IMPORTS #########################
import requests
from zipfile import ZipFile
from shutil import rmtree, copyfile
import os
import sys
import subprocess
#########################################################

####################### GLOBALS #########################
GITHUB_RAW      = "https://raw.githubusercontent.com/joan2937/pigpio/master/"
VERSION_REQFILE = "pigpio.h"
VERSION_TAG     = "PIGPIO_VERSION"
GITHUB_ARCHIVE  = "https://github.com/joan2937/pigpio/archive/"
GITHUB_PRE      = "v"
GITHUB_EXT      = ".zip"
FOLDER_PRE      = "pigpio-"
#https://github.com/joan2937/pigpio/tree/v76
#https://github.com/joan2937/pigpio/archive/v76.zip
BUILD_LOC       = "/var/pigpio_build/"
VERSIONFILE_INS = "/opt/pigpio_builder/pigpio_version"
VERSIONFILE_CUR = "/opt/pigpio_builder/pigpio_current"
PIGPIOD_LOC     = "/usr/local/bin/pigpiod"
PIGPIOD_ALT_LOC = "/usr/bin/pigpiod"
SERVICE_LOC     = "/etc/systemd/system/"
SERVICE_FILE    = "pigpiod.service"
SERVICE_SRC     = "/util/"
#########################################################

###################### FUNCTIONS ########################
def process_current_version(update):
    if update:
        version = obtain_current_version()
        set_current_version(version)
    else:
        version = get_current_version()
        if version == 0:
            version = obtain_current_version()
            set_current_version(version)

    return version

def obtain_current_version():
    version = None
    r = requests.get(GITHUB_RAW+VERSION_REQFILE)
    for line in r.text.split('\n'):
        if VERSION_TAG in line:
            for content in line.split(" "):
                try:
                    i = int(content)
                    f = float(content)
                    if i == f:
                        version = i
                    else:
                        version = f
                except:
                    pass
    return version

def get_current_version():
    version = None
    try:
        with open(VERSIONFILE_CUR, 'r') as verfile:
            version = int(verfile.read())
    except:
        version = 0
    return version

def set_current_version(version):
    with open(VERSIONFILE_CUR, 'w') as verfile:
        verfile.write(str(version))

    return version

def get_installed_version():
    version = None
    try:
        with open(VERSIONFILE_INS, 'r') as verfile:
            version = int(verfile.read())
    except:
        version = 0
    return version

def set_installed_version(version):
    with open(VERSIONFILE_INS, 'w') as verfile:
        verfile.write(str(version))

    return version

def download_build(version):
    filename = GITHUB_PRE + str(version) + GITHUB_EXT
    url = GITHUB_ARCHIVE + filename
    fileloc = BUILD_LOC + filename

    if not os.path.isdir(BUILD_LOC):
        os.mkdir(BUILD_LOC)

    r = requests.get(url, allow_redirects=True)
    open(fileloc, 'wb').write(r.content)

    with ZipFile(fileloc, 'r') as zipObj:
        # Extract all the contents of zip file in different directory
        zipObj.extractall(BUILD_LOC)

def build(version):
    folder = BUILD_LOC + FOLDER_PRE + str(version)

    out = subprocess.run(["make"], stderr=sys.stderr, stdout=sys.stdout, cwd = folder)

    if out.returncode != 0:
        print("Error building pigpio, not installing")
        return

    out = subprocess.run(["make","install"], stderr=sys.stderr, stdout=sys.stdout, cwd = folder)

    if out.returncode != 0:
        print("Error installing pigpio, pigpio not installed")

    return

def cleanup():
    rmtree(BUILD_LOC)

    return

def update_pigpiodloc():
    existLoc    = os.path.exists(PIGPIOD_LOC)
    existAltLoc = os.path.exists(PIGPIOD_ALT_LOC)
    if existLoc and existAltLoc:
        pass
    elif existLoc:
        os.symlink(existLoc, existAltLoc)
    elif existAltLoc:
        os.symlink(existAltLoc, existLoc)
    else:
        print("Error pigpiod executable doesn't exist")
    return

def start_service(version):
    src_folder = BUILD_LOC + FOLDER_PRE + str(version) + SERVICE_SRC + SERVICE_FILE
    dst_folder = SERVICE_LOC + SERVICE_FILE

    copyfile(src_folder, dst_folder)

    out = subprocess.run(["systemctl","enable", SERVICE_FILE], stderr=sys.stderr, stdout=sys.stdout)

    if out.returncode != 0:
        print("Error enabling pigpio service")

    out = subprocess.run(["systemctl","start", SERVICE_FILE], stderr=sys.stderr, stdout=sys.stdout)

    if out.returncode != 0:
        print("Error starting pigpio service")

    return

#########################################################

######################### MAIN ##########################
if __name__ == "__main__":
    if os.getuid() != 0:
        print("This program needs to be run as super user")
        print("try: sudo update_pigpio")
        exit(2)

    version = 0
    installed_version = get_installed_version()
    if len(sys.argv) > 1:
        if sys.argv[1] == "help" or sys.argv[1] == "-h" or sys.argv[1] == "--help":
            print("pigpio_builder")
            print("This program automatically builds the latest release of pigpio")
            print("Options:")
            print("help, -h or --help: print this help file and exit")
            print("force             : force update, even if no new version is available")
            print("update            : only prints message when an update is available")
            print("upgrade           : installs update when available")
            print("<no arguments>    : installs update when available (more verbose)")
            exit()
        elif sys.argv[1] == "force":
            version = process_current_version(True)
            print("Forcing update, version: " + str(version))
        elif sys.argv[1] == "update":
            version = process_current_version(True)
            if installed_version != version:
                print("pigpio update available, version: " + str(version) + ", please run update_pigpio")
            exit()
        elif sys.argv[1] == "upgrade":
            version = process_current_version(False)
            if installed_version != version:
                print("Installing pigpio update, version: " + str(version))
            else:
                exit()
    else:
        if sys.argv[0] == "update_pigpio":
            version = process_current_version(False)
        else:
            version = process_current_version(True)
        if installed_version == version:
            print("No update available")
            exit()
        else:
            print("Installing pigpio update, version: " + str(version))
    download_build(version)
    build(version)
    set_installed_version(version)
    update_pigpiodloc()
    start_service(version)
    cleanup()
