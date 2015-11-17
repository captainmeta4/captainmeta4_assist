import praw
from collections import deque
from collections import OrderedDict
import re
import os

r=praw.Reddit('public removal logs for /r/politics by /u/captainmeta4')

source = "politics"
mirror = "politicsremovals"
username = "politicsmoderatorbot"


source_sub = r.get_subreddit(source)
mirror_sub = r.get_subreddit(mirror)

compose_link = re.compile("\[(.+)\]\(.*compose.*\)")

class Bot():

    def __init__(self):

        self.already_done=deque([],maxlen=200)
        self.mapping = OrderedDict([])

        self.login()

    def login(self):

        r.login(username,os.environ.get('password'), disable_warning=True)

    def new_log_entry(self, fullname):

        submission = r.get_info(thing_id=fullname)
        
        url = "http://np.reddit.com/r/"+source+"/comments/"+submission.id+"/-/"

        #make the new submission
        new = r.submit(mirror_sub, submission.title, url = url)

        #add submission ids to mapping
        self.mapping[submission.fullname] = new.fullname
        while len(self.mapping) > 100:
            self.mapping.popitem(last=False)

        #approve the new submission so it stays out of my unmod
        new.approve()

        return new

    def find_entry(self, submission_fullname):
        #given a source submission, find the corresponding log entry
        #if it doesn't exist, creates new one

        submission_id = submission_fullname.split(sep="_")[1]

        query = "url:reddit.com/r/"+source+"/comments/"+submission_id
        for submission in mirror_sub.search(query, sort="new", limit=1):
            return submission
            break
        else:
            return None
        
    def get_entry(self, submission_fullname):
        #given a source submission, returns the corresponding log entry
        #checks cache first, then searches

        if submission_fullname in self.mapping:
            return r.get_info(thing_id=self.mapping[submission_fullname])
        else:
            return self.find_entry(submission_fullname)


    def unending_mod_log(self):
        while True:
            actions = []
            for action in source_sub.get_mod_log(limit=100):
                if action.id in self.already_done:
                    continue
                self.already_done.append(action.id)
                actions.append(action)

            actions.reverse()
            for action in actions:
                yield action

    def quote_text(self, text):
        #extracts the removal reason from the comment text

        output = re.sub(compose_link, "\\1",text)

        output = output.replace("\n","\n> ")
        output = "> "+output
        
        return output


    def log_actions(self):

        for action in self.unending_mod_log():
            
            #ignore actions that are not link approvals, link removals, or link flairs
            if action.action not in ["removelink", "approvelink", "distinguish", "editflair"]:
                continue

            #ignore automod
            if action.mod =="AutoModerator":
                continue
            
            

            #for approvals/removals, get log entry.
            #for distinguishes, make sure it's a top level comment; otherwise skip
            if action.action in ["approvelink","removelink"]:
                log_entry = self.get_entry(action.target_fullname)
                target = r.get_info(thing_id = action.target_fullname)
            elif action.action in ["distinguish"]:
                target = r.get_info(thing_id = action.target_fullname)
                if not target.parent_id.startswith("t3_"):
                    continue
                log_entry = self.get_entry(target.parent_id)
            elif action.action in ["editflair"]:
                if not action.target_fullname.startswith("t3_"):
                    continue
                target = r.get_info(thing_id = action.target_fullname)
                log_entry = self.get_entry(action.target_fullname)

            #ignore approvals/distinguishes that don't have a corresponding log entry
            if (action.action in ["approvelink","distinguish","editflair"] and
                log_entry is None):
                continue

            #make a new log entry if we don't have one already
            if (action.action in ["removelink"] and
                log_entry is None):
                log_entry = self.new_log_entry(action.target_fullname)


            #flair log entries
            if (action.action =="removelink"
                or (action.action == "editflair" and (target.banned_by is not None))):

                #see what the linkflair should be on removed posts
                text= "removed"
                css_class = "removed red"

                #check for spammed
                if action.details == "removed spam":
                    text = "Spam"
                    css_class = "removed pink"

                #check for no text
                elif (target.link_flair_text is not None
                    and target.link_flair_text != ""):
                    text = target.link_flair_text
                
                log_entry.set_flair(flair_text = text, flair_css_class=css_class)

            elif action.action == "approvelink":
                if (log_entry.link_flair_css_class != "approved green"
                    or log_entry.link_flair_text != "approved"):
                    log_entry.set_flair(flair_text = "approved", flair_css_class = "approved green")
                continue

            
            elif action.action == "distinguish":
                text = "The following was provided by a moderator, and may be useful to understanding this removal:\n\n"
                text += self.quote_text(target.body)
                log_entry.add_comment(text).distinguish()
            

if __name__=="__main__":
    modbot=Bot()
    modbot.log_actions()

