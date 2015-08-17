import praw
import urllib.parse as urlparse
import os

#Initiate reddit
r=praw.Reddit(user_agent='reddit repost detector running under /u/captainmeta4')

#Set globals
username='captainmeta4'

subredditname='mod'

requires_params=[
    'c-span.org',
    'defense.gov',
    'house.gov',
    'news-republic.com',
    'senate.gov',
    'quinnipiac.edu',
    'youtu.be',
    'youtube.com'
    ]

ignore_subreddits=[
    'xkcd'
    ]

#Feature not yet deployed
#zero_false_positive=[
#    'bostonglobe.com',
#    'cnn.com',
#    'latimes.com',
#    'nytimes.com'
#    'washingtonpost.com',
#    'vox.com'
#    ]

class bot():

    def login(self):
        r.login(username,os.environ.get('password'))

    def process_submissions(self):

        #Collect unending submission stream
        for submission in praw.helpers.submission_stream(r, subredditname, limit=100, verbosity=0):
            print('checking '+submission.title)
            
            #ignore self-posts
            if submission.is_self:
                continue
            
            #ignore certain subreddits
            if submission.subreddit.display_name in ignore_subreddits:
                continue

            #break down url
            ParsedURL = urlparse.urlparse(submission.url)

            #strip params and query unless it's a site known to need them
            if any(entry in submission.domain for entry in requires_params):
                params=ParsedURL[3]
                query=ParsedURL[4]
            else:
                params=''
                query=''
                
            #strip mobile. subdomain away from netloc
            netloc=ParsedURL[1]
            netloc=netloc.replace('mobile.','',1)
                
            #strip fragments and assemble url to search for,
            NewParsedURL=urlparse.ParseResult(
                scheme=ParsedURL[0],
                netloc=netloc,
                path=ParsedURL[2],
                params=params,
                query=query,
                fragment=''
                )
            url=urlparse.urlunparse(NewParsedURL)
            
            #strip away schema
            url=url.replace('http://','',1)
            url=url.replace('https://','',1)
            #print(url)
            
            #create search string
            search = "url:"+url

            #Search subreddit for other posts that match            
            for searchresult in r.search(search,subreddit=submission.subreddit, sort='New'):

                #Ignore the original post
                if searchresult.id == submission.id:
                    continue

                #Ignore newer posts - only flag if there's an older post
                if searchresult.created_utc > submission.created_utc:
                    continue

                #Flag as possible repost and break out of search results
                print('repost detected')
                submission.report(reason='Bot - possible repost - http://redd.it/'+searchresult.id)
                break

    def run(self):
        self.login()
        self.process_submissions()

if __name__=='__main__':
    modbot=bot()
    modbot.run()
