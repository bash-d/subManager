#!/usr/bin/python3
from urllib.request import urlopen
from pathlib import Path
import xml.etree.ElementTree as ET
import re
import fileinput
import argparse
import sys


def parseFile(subFile):
    try:
        tree = ET.parse(subFile)
        root = tree.getroot()
        outline = root.find('body').find('outline')
    except Exception as e:
        exit("{} Could not parse file \'{}\'".format(e, subFile))

    if outline == None:
        exit("\'{}\' has improper XML format".format(subFile))
    else:
        subDict = {}

        for channel in next(outline.iter()):
            subDict[channel.get('text')] = channel
        
        return(outline, tree, subDict)


def createSubFile():
    subFile = str(input("No subscription file specified enter name for new file [subscription_manager]: ") or 'subscription_manager')

    if Path(subFile).is_file():
        choice = str(input("\'{}\' already exists would you like to overwrite it [y/N]: ".format(subFile)) or 'n').lower()
        if choice != 'y':
            exit()

    opml = ET.Element('opml', version="1.1")
    body = ET.SubElement(opml, 'body')
    outline = ET.SubElement(body, 'outline', text="YouTube Subscriptions", title="YouTube Subscriptions")
    tree = ET.ElementTree(opml)
    try:
        tree.write(subFile)
    except Exception as e:
        print("{} Could not create file \'{}\'".format(e, subFile))
    return(subFile)


def addSub(subFile, url):
    outline, tree, subDict = parseFile(subFile)

    try:
        request = urlopen(url)
        response = request.read()
    except:
        print("Could not reach URL")

    if 'This video is restricted' in response.decode():
        print("Video is restricted")
        return

    try:
        channelName = re.search('"name": "(.+)"', response.decode()).group(1)
    except:
        print("Channel name not found")
        return
    try:
        channelId = re.search('"channelId" content="(.+)"', response.decode()).group(1)
    except:
        print("Channel ID not found")
        return

    if channelId in open(subFile).read():
        print("\'{}\' already in \'{}\'".format(channelName, subFile))
    else:
        # add rss entry to file
        outline.append((ET.fromstring('<outline text="{}" title="{}" type="rss" xmlUrl="https://www.youtube.com/feeds/videos.xml?channel_id={}" />'.format(channelName, channelName, channelId))))
        try:
            tree.write(subFile)
            print("\'{}\' added to \'{}\'".format(channelName, subFile))
        except Exception as e:
            print("{} Could not add \'{}\' to file \'{}\'".format(e, channelName,  subFile))


def removeSub(subFile, removeName):
    outline, tree, subDict = parseFile(subFile)

    if removeName in subDict:
        outline.remove(subDict[removeName])
        try:
            tree.write(subFile)
            print("\'{}\' removed from \'{}\'".format(removeName, subFile))
        except Exception as e:
            print("{} Could not remove \'{}\' from \'{}\'".format(e, removeName, subFile))        
    else:
        print("Could not find \'{}\' in \'{}\'".format(removeName, subFile))
        
    
def listSubs(subFile):
    subDict = parseFile(subFile)[2]
    print("Youtube Subscriptions")
    print("---------------------")
    for channel in subDict.keys():
        print(channel)

parser = argparse.ArgumentParser()
command_group = parser.add_mutually_exclusive_group()
parser.add_argument('file', help="subscription_manager file to use, if not specified one will be created", nargs='?')
command_group.add_argument('-a', '--add', metavar="video/channel URL", help="add channel to subscriptions file")
command_group.add_argument('-r', '--remove', metavar="channel", help="remove channel from subscriptions file")
parser.add_argument('-l', '--list', help="list subscriptions", action='store_true')
args = parser.parse_args()

subFile = args.file

if args.add:
    if args.file:
        addSub(args.file, args.add)
    else:
        newFile = createSubFile()
        addSub(newFile, args.add)

if args.remove:
    if not args.file:
        parser.error("argument -r/--remove: requires a file")
    else:
        removeSub(args.file, args.remove)

if args.list:
    if not args.file:
        parser.error("argument -l/--list: requires a file")
    else:
        listSubs(args.file)
