import praw
import requests
import os
import math
from collections import deque
import time
import re
import signal
import sys

#Initialize reddit
r=praw.Reddit(user_agent="Content age enforcement bot by /u/captainmeta4")
username = "captainmeta4"
master_subreddit = "captainmeta4bots"

#Embed.ly stuff
embedly_key=os.environ.get('key')

#graceful exit
def sigterm_handler(signal, frame):
    r.edit_wiki_page(master_subreddit,"assist",str(modbot.already_done))
signal.signal(signal.SIGTERM, sigterm_handler)

class Bot():

    def initialize(self):
        r.login(username,os.environ.get('password'))
        
        self.already_done=eval(r.get_wiki_page(master_subreddit,"assist").content_md)
        self.options=eval(r.get_wiki_page(master_subreddit,"content_age").content_md)
    

    
    
    
    def process_politics_submissions(self):
    #Enforces content age rule in /r/politics
    
        print ("processing /r/politics submissions")
        
        #Trick to avoid eating the embedly API limit
        limit=1
        for submission in r.get_subreddit('politics').get_new(limit=limit):
        limit=100
            #Avoid duplicate work
            if (submission.id in self.already_done
                or submission.fullname in self.already_done):
                continue

            self.already_done.append(submission.fullname)

            print("checking "+submission.title)

            #ignore self_posts:
            if submission.is_self:
                continue

            #Get the submission url
            url=submission.url

            #Create params
            params={'url':url,'key':embedly_key}

            #Hit the embed.ly API for data
            data=requests.get('http://api.embed.ly/1/extract',params=params)

            #Get content timestamp
            try:
                content_creation = data.json()['published']
            except:
                continue

            #Pass on content that does not have a timestamp
            if content_creation == None:
                continue

            #Divide the creation timestamp by 1000 because embed.ly adds 3 extra zeros for no reason
            content_creation = content_creation / 1000
            
            #sanity check for if embedly fucks up
            if content_creation < 0:
                continue

            #Get the reddit submission timestamp
            post_creation = submission.created_utc

            #Find content age, in days
            age = math.floor((post_creation - content_creation) / (60 * 60 * 24))

            #Pass on submissions that are new enough
            try:
                if age <= self.options[submission.subreddit.display_name.lower()]:
                    continue
            except KeyError:
                self.options[submission.subreddit.display_name.lower()]=365

            #At this point we know the post breaks the recent content rule
            print("http://redd.it/"+submission.id+" - "+submission.title)

            #Remove the submission
            try:
                submission.remove()
            
                #Leave a distinguished message
                msg=("Hi "+submission.author.name+". Thank you for participating in /r/Politics. However, [your submission]("+submission.permalink+") has been removed for the following reason(s):"+
                     "\n\n* [Out of Date](http://www.reddit.com/r/politics/wiki/rulesandregs#wiki_the_.2Fr.2Fpolitics_on_topic_statement): /r/politics is for **current** US political news and information that has been published within the last 45 days."+
                     "\n\nIf you have any questions about this removal, please feel free to [message the moderators.](https://www.reddit.com/message/compose?to=/r/politics&subject=Question regarding the removal of this submission by /u/"+submission.author.name+"&message=I have a question regarding the removal of this [submission.]({"+submission.permalink+"}\))")
                
                submission.add_comment(msg).distinguish()
                submission.set_flair(flair_text="Out of Date")
            except:
                pass
    
    def process_my_comments(self):
    #personal commands
        
        for comment in r.get_redditor(username).get_comments(sort='new',limit=100):
            
            #Avoid duplicate work
            if comment.fullname in self.already_done:
                continue
            
            self.already_done.append(comment.fullname)
            
            #global ban
            if comment.body=='!global':
                
                #get parent object author
                parent_author = r.get_info(thing_id=comment.parent_id).author
                
                for subreddit in r.get_my_moderation(limit=none):
                    try:
                        subreddit.add_ban(parent_author)
                    except:
                        pass
            

    def run(self):
        self.initialize()
        while True:
            self.process_politics_submissions()
            self.process_my_comments()

            

if __name__=='__main__':
    modbot=Bot()
    modbot.run()
