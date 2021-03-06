import atexit
import html
import configparser
import os
import pickle
import re
import time
import urllib.error
import urllib.request

import praw

HTTPRE = re.compile('http[s]?://', re.IGNORECASE)
DOMRE = re.compile('\.\w{2,20}', re.IGNORECASE)
BLACKLIST = ['LE_TROLLFACEXD', 'figuratively_hilter', 'Text_Reader_Bot']

FOOTER = '''

*****
[IsItDownBot](https://github.com/JamieMagee/IsItDownBot) \
by [Jammie1](http://reddit.com/u/Jammie1)
'''


def exit_handler():
    if fileOpened:
        pickle.dump(already_done, f)
        f.close()


atexit.register(exit_handler)


def valid_response_code(code):
    if (code == 200) or (code == 301) or (code == 302):
        return True
    else:
        return False


def isdone(comment):
    if comment.id not in already_done and comment.author.name != "IsItDownBot":
        comment_replies = comment.replies
        for reply in comment_replies:
            if reply.author.name == "IsItDownBot":
                already_done.append(comment.id)
                return True
        return False
    else:
        return True


def reply(text, comment):
    while True:
        try:
            comment.reply(text)
            break
        except praw.errors.RateLimitExceeded as error:
            print("Doing too much, sleeping for " + str(error.sleep_time))
            time.sleep(error.sleep_time)
        except Exception as e:
            print("Exception occurred while replying: " + str(e))
            time.sleep(3)


class Url:
    def __init__(self, domain):
        if domain.find("http%3A//") is not -1:
            domain = domain.split("http%3A//")[1]

        self.original_domain = domain
        self.domain = self.clean_url(domain)

    @staticmethod
    def clean_url(domain):
        domain = html.escape(domain)
        domain.encode("utf-8")

        if HTTPRE.match(domain) is None:
            domain = 'http://' + domain

        pieces = domain.split("/")

        while len(pieces) > 3:
            pieces.pop()

        domain = "/".join(pieces)

        return domain

    def missingdomain(self):
        if DOMRE.search(self.domain) is None:
            return True
        else:
            return False


already_done = []
if os.path.isfile('commentcache'):
    f = open('commentcache', 'r+')
    if f.tell() != os.fstat(f.fileno()).st_size:
        already_done = pickle.load(f)
    f.close()
f = open('commentcache', 'w+')
fileOpened = True

r = praw.Reddit('/u/IsItDownBot by /u/Jammie1')

if os.path.isfile('settings.cfg'):
    config = configparser.ConfigParser(interpolation=None)
    config.read('settings.cfg')
    username = config.get('auth', 'username')
    password = config.get('auth', 'password')
else:
    username = os.environ['REDDIT_USERNAME']
    password = os.environ['REDDIT_PASSWORD']

COMRE = re.compile('/u/' + username + ' (.*)', re.IGNORECASE)

print('[*] Logging in as %s...' % username)
r.login(username, password)
print('[*] Login successful...')

while True:
    print('[*] Getting comments...')

    for message in r.get_mentions():
        if COMRE.search(message.body) and message.author.name not in BLACKLIST and not isdone(message):
            u = Url(COMRE.search(message.body).group(1))
            if u.missingdomain():
                print("Huh? " + u.domain + " doesn't look like a site on the interwho.")
                reply("Huh? " + u.domain + " doesn't look like a site on the interwho." + FOOTER, message)
            else:
                try:
                    response = urllib.request.urlopen(u.domain).code
                except urllib.error.URLError:
                    print("Huh? " + u.domain + " doesn't look like a site on the interwho.")
                    reply("Huh? " + u.domain + " doesn't look like a site on the interwho." + FOOTER, message)
                else:
                    if valid_response_code(response):
                        print("It's just you. " + u.domain + " is up.")
                        reply("It's just you. " + u.domain + " is up." + FOOTER, message)
                    else:
                        print("It's not just you! " + u.domain + " looks down from here.")
                        reply("It's not just you! " + u.domain + " looks down from here." + FOOTER, message)
        message.mark_as_read()
        already_done.append(message.id)
    time.sleep(2)
