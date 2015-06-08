import praw
import requests
import os
import math
from collections import deque
import time
import re

#Initialize reddit
r=praw.Reddit(user_agent="Content age enforcement bot by /u/captainmeta4")
username = "Content_Age_Bot"
master_subreddit = "captainmeta4bots"

#Embed.ly stuff
embedly_key=os.environ.get('key')

class Bot():

    def initialize(self):
        r.login(username,os.environ.get('password'))
        self.already_done=deque([],maxlen=200)

        self.options=eval(r.get_wiki_page(master_subreddit,"content_age").content_md)

    def check_messages(self):

        print('checking messages')

        for message in r.get_unread(limit=None):

            message.mark_as_read()
            
            #Ignore post/comment replies
            if (message.subject=="post reply"
                or message.subject=="comment reply"):
                continue
            
            #Assume it's a mod invite
            try:
                message.subreddit.accept_moderator_invite()

                print('accepted mod invite for /r/'+message.subreddit.display_name)

                msg=("Hello, moderators of /r/"+message.subreddit.display_name+
                     "\n\nI am a bot that checks the age of submitted content, and automatically removes content that is too old."+
                     "\n\nBy default, my threshold is 365 days. To adjust my threshold, send me a PM with your subreddit name as the subject, and the threshold as the body"+
                     "\n\nPlease note that I require Posts permissions for proper functionality."
                     "\n\nFeedback may be directed to my creator, /u/captainmeta4")

                r.send_message(message.subreddit, "Introduction",msg)

                self.options[subreddit.display_name.lower()]= 365

                r.edit_wiki_page(master_subreddit,"content_age",str(self.options))

                continue
                
            except:
                pass

            #Now do subreddit configs
            try:
            
                subredditname=message.subject

                if message.author not in r.get_moderators(subredditname):
                    message.reply("You are not a moderator of that subreddit")
                    continue

                #check message body for junk
                if re.search("^\\d{1,3}$",message.body) == None:
                    message.reply("1There was a problem, and I wasn't able to make sense of your message. (Error code: 1)")

                threshold=eval(message.body)

                self.options[subredditname.lower()]= threshold

                r.edit_wiki_page(master_subreddit,"content_age",str(self.options))

                msg=("Threshold Update","The age threshold for /r/"+subredditname+" has been set to "+str(threshold)+" days by /u/"+message.author.name)

                r.send_message(r.get_subreddit(subredditname),"Threshold Update",msg)
                print(msg)
                
            except:
                message.reply("There was a problem, and I wasn't able to make sense of your message. (Error code: 2)")
                

    def process_submissions(self):
        print ("processing submissions")

        for submission in r.get_subreddit("politics").get_new(limit=200):

            #Avoid duplicate work
            if submission.id in self.already_done:
                continue

            self.already_done.append(submission.id)

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
                     "* [Out of Date](http://www.reddit.com/r/politics/wiki/rulesandregs#wiki_the_.2Fr.2Fpolitics_on_topic_statement): /r/politics is for **current** US political news and information that has been published within the last 45 days."+
                     "If you have any questions about this removal, please feel free to [message the moderators.](https://www.reddit.com/message/compose?to=/r/politics&subject=Question regarding the removal of this submission by /u/"+submission.author.name+"&message=I have a question regarding the removal of this [submission.]({"+submission.permalink+"}\))
                
                submission.add_comment(msg).distinguish()
                submission.set_flair(flair_text="Out of Date")
            except:
                pass

    def run(self):
        self.initialize()

        while 1:
            #self.check_messages()
            self.process_submissions()

            

if __name__=='__main__':
    modbot=Bot()
    modbot.run()
