import praw
import urllib.parse as urlparse
import os

#Initiate reddit
r=praw.Reddit(user_agent='/r/politics repost detector')

#Set globals
username='captainmeta4'

subredditname='politics'

requires_params=[
    'youtu.be',
    'youtube.com'
    ]


class bot():

    def login(self):
        r.login(username,os.environ.get('password'))

    def process_submissions(self):

        #Collect unending submission stream
        for submission in praw.helpers.submission_stream(r, subredditname, limit=100, verbosity=0):
            print('checking '+submission.title)

            #break down url
            ParsedURL = urlparse.urlparse(submission.url)

            #strip params and query unless it's a site known to need them
            if submission.domain in requires_params:
                params=ParsedURL[3]
                query=ParsedURL[4]
            else:
                params=''
                query=''
            
                
            #strip fragments and assemble url to search for,
            NewParsedURL=urlparse.ParseResult(
                scheme=ParsedURL[0],
                netloc=ParsedURL[1],
                path=ParsedURL[2],
                params=params,
                query=query,
                fragment=''
                )
            url=urlparse.urlunparse(NewParsedURL)

            #print(url)
            
            #create search string
            search = "url:"+url

            #Search subreddit for other posts that match            
            for searchresult in r.search(search,subreddit=subredditname, sort='New'):

                #Ignore the original post
                if searchresult.id == submission.id:
                    continue

                #Ignore newer posts - only flag if there's an older post
                if searchresult.created_utc > submission.created_utc:
                    continue

                #Flag as possible repost and break out of search results
                print('repost detected')
                submission.report(reason='Bot in testing - possible repost - http://redd.it/'+searchresult.id)
                break

    def run(self):
        self.login()
        self.process_submissions()

if __name__=='__main__':
    modbot=bot()
    modbot.run()
