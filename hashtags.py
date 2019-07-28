import requests

class HashtagGrabber():
    def getHashtags(self,word):
        data = {"filter":"random",
                "keyword":word}
        headers = {"X-Requested-With":"XMLHttpRequest",
                   "User-Agent":"Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36",
                   "Referer":"https://all-hashtag.com/hashtag-generator.php",
                   "Host":"all-hashtag.com",
                   "Content-Type":"application/x-www-form-urlencoded;charset=UTF-8",
                   "Accept-Language":"en-GB;en;q=0.5",
                   "Accept-Encoding":"gzip, deflate, br",
                   "Accept":"*/*"}

        # Go to some webste and grab the best hashtags for the said word
        r = requests.post("https://all-hashtag.com/library/contents/ajax_generator.php", data=data, headers=headers)

        rawHTML = str(r.content)

        textToSearch = "class=\"copy-hashtags\">"

        startPos = rawHTML.index(textToSearch) + len(textToSearch)
        endPos = rawHTML.index("</div>", startPos)

        return (rawHTML[startPos:endPos])