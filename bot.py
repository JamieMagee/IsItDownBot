import praw, urllib2, re, cgi, ConfigParser, time, os

HTTPRE = re.compile('http[s]?:\/\/', re.IGNORECASE)
DOMRE = re.compile('\.\w{2,20}')
COMRE = re.compile('is (.*) down\?', re.IGNORECASE)

FOOTER = '''

*****
[IsItDownBot](http://reddit.com/u/IsItDownBot) \
bot by [Jammie1](http://reddit.com/u/Jammie1)
'''

def valid_response_code(code):
  if (code == 200) or (code == 301) or (code == 302):
    return True
  else:
    return False

class Url:
  def __init__(self, domain):
    if domain.find("http%3A//") is not -1:
      domain = domain.split("http%3A//")[1]

    self.original_domain = domain
    self.domain = self.clean_url(domain)

  def clean_url(self, domain):
    domain = cgi.escape(domain)
    domain.encode("utf-8")

    if HTTPRE.match(domain) == None:
      domain = 'http://' + domain

    pieces = domain.split("/")

    while (len(pieces) > 3):
      pieces.pop()

    domain = "/".join(pieces)

    return domain

  def missingdomain(self):
    if DOMRE.search(self.domain) == None:
      return True
    else:
      return False

r = praw.Reddit('/u/IsItDownBot by /u/Jammie1')

if os.path.isfile('settings.cfg'):
  config = ConfigParser.ConfigParser()
  config.read('settings.cfg')
  username = config.get('auth', 'username')
  password = config.get('auth', 'password')
else:
  username = os.environ['REDDIT_USERNAME']
  password = os.environ['REDDIT_PASSWORD']

print '[*] Logging in as %s...' % username
r.login(username, password)
print '[*] Login successful...\n'

already_done = set()
while True:
  subreddit = r.get_subreddit('jammie1')
  subreddit_comments = subreddit.get_comments()
  print '[*] Getting submissions...\n'

  for comment in subreddit_comments:
    if COMRE.search(comment.body) and comment.id not in already_done:
      u = Url(COMRE.search(comment.body).group(1))
      if u.missingdomain():
        print("Huh? " + u.domain + " doesn't look like a site on the interwho.")
        comment.reply("Huh? " + u.domain + " doesn't look like a site on the interwho." + FOOTER)
        already_done.add(comment.id)
      else:
        try:
          response = urllib2.urlopen(u.domain).code
        except urllib2.URLError:
          print("Huh? " + u.domain + " doesn't look like a site on the interwho.")
          comment.reply("Huh? " + u.domain + " doesn't look like a site on the interwho." + FOOTER)
          already_done.add(comment.id)
        else:
          if valid_response_code(response):
            print("It's just you. " + u.domain + " is up.")
            comment.reply("It's just you. " + u.domain + " is up." + FOOTER)
            already_done.add(comment.id)
          else:
            print("It's not just you! " + u.domain + " looks down from here.")
            comment.reply("It's not just you! " + u.domain + " looks down from here." + FOOTER)
            already_done.add(comment.id)
  time.sleep(2)