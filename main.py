# Fun script to simulate my walks around UK
# Regular updates are to be posted to instagram 
# The script is going to run from some host

#!/usr/bin/python3.6
#-*-coding: utf-8-*-
import requests,json,csv, random
from datetime import datetime as d
import datetime
import unicodedata
from InstagramAPI import InstagramAPI
import osm_tiles
import hashtags
import os
from service_google import GDrive


class insta_bot():
    def __init__(self,username,password):
        self.api = InstagramAPI(username,password)

        if(self.api.login()):
            self.api.getSelfUserFeed()
        else:
            print("Can't login!")
            
    def upload_pictures(self,pics,captionText):
        media = []
        for pic in pics:
            media.append({"type":"photo",
                          "file":pic})
        self.api.uploadAlbum(media,caption=captionText)

def generate_caption():
    ht = hashtags.HashtagGrabber()
    # Get random word
    word = requests.get("https://randomwordgenerator.com/json/words.json").json()
    word = word["data"]
    i = random.randint(0,len(word)-1)
    word = word[i]["word"]
    hts = ht.getHashtags(word)
    caption = "I am not sure where I am going. {}".format(hts)
    return caption
    
def main():
    g = GDrive()
    # Download files from Google drive
    print("Downloading files")
    a=g.download_files()
    
    tiles = osm_tiles.Traveller()
    
    loginDetails = [os.environ['INSTA_USR'],os.environ['INSTA_PAS']]

    # Login into my account
    bot = insta_bot(loginDetails[0],loginDetails[1])
    caption = generate_caption()
    # Upload pictures
    print("Uploading pictures to Instagram")
    bot.upload_pictures(["o.jpg","o2.jpg","o3.jpg"],caption)
    
    # Upload modified files to Google drive
    print("Uploading files to GDrive")
    g.upload_files(["stats.csv","history.csv","destinations.csv"])
    print("Done")
