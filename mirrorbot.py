#[wip]

import praw
import json
import time
from collections import deque
from collections import OrderedDict

###   CONFIGS   ###

#praw
r=praw.Reddit('Subreddit mirror bot')

#Subreddit to scrape
source = r.get_subreddit('watchpeopledie')

#Subreddit to act as mirror
mirror = r.get_subreddit('wpd_de')

#Already-processed and mappings. Eval is necessary due to use of deques and ordereddicts
data = json.loads(r.get_wiki_page('captainmeta4bots','mirrorbot').content_md)
for entry in data:
    data[entry]=eval(data[entry])


### END CONFIGS ###


class Bot():

    def save_cache(self):

        #We're treating the mappings as a deque so chop down to 1000
        while len(data['mappings']) > 1000:
            data['mappings'].popitem(last=False)
        
        #re-stringify data and save to reddit
        cache = data
        for entry in cache:
            cache[entry]=str(cache[entry])
        r.edit_wiki_page('captainmeta4bots','mirrorbot',json.dumps(cache))

    def mirror_submission(self, submission):
        
        #mirror the post
        if submission.is_self:
            post = r.submit(mirror, title=submission.title, text = submission.selftext, resubmit=True)
        else:
            post = r.submit(mirror, title=submission.title, url=submission.url, resubmit=True)

        #Add id pairing to mappings

        data['mappings'][submission.fullname] = post.fullname

        return post

    def mirror_new(self):
        #Check /new for any submissions and mirror them.
        for submission in source.get_new(limit=100):

            #avoid duplicate posts
            if submission.fullname in data['mappings']:
                continue

            self.mirror_submission(submission)


    def mirror_mod(self):
        #Mirror certain types of mod actions

        #Keep a temporary list of things that have already been acted on this cycle.
        #This ensures that in the case of multiple approve/remove, only the most recent action is mirrored
        items_acted_on = []
        users_acted_on = []
        automod_updated = False
        
        #Check /about/modlog and mirror actions as needed
        for entry in source.get_mod_log(limit=100):

            #ignore most actions
            if entry.action not in ['approvelink','removelink','banuser','unbanuser','wikirevise']:
                continue

            #Don't act on the same entry twice
            if entry.id in data['modlog']:
                continue

            #Don't execute an old action over a newer action
            if (entry.action in ['approvelink','removelink']
                and entry.target_fullname in items_acted_on):
                continue
            elif (entry.action in ['banuser','unbanuser']
                  and entry.target_author in users_acted_on):
                continue
            elif (entry.action =='wikirevise'
                  and automod_updated):
                continue

            #begin mirroring process

            #mirror approvals/removals
            if entry.action in ['approvelink','removelink']:

                #avoid conflicting actions
                items_acted_on.append(entry.target_fullname)

                #Find corresponding mirror post
                if entry.target_fullname not in data['mappings']:
                    continue
                mirror_post = r.get_info(data['mappings'][entry.target_fullname])

                if entry.action == 'approvelink':
                    mirror_post.approve()
                if entry.action == 'removelink':
                    mirror_post.remove()
                
            #mirror bans/unbans    
            elif entry.action in ['banuser','unbanuser']:
                users_acted_on.append(entry.target_author)

                if entry.action=='banuser':
                    mirror.add_ban(entry.target_author)
                elif entry.action=='unbanuser':
                    mirror.remove_ban(entry.target_author)

            #mirror automod config, keeping any mirror-specific rules at the top
            if (entry.action == 'wikirevise'
                and entry.details == 'Updated AutoModerator configuration'
                and not automod_updated):
                
                source_automod = r.get_wiki_page(source,'config/automoderator').content_md
                mirror_automod = r.get_wiki_page(mirror,'config/automoderator').content_md
                
                split_string = '#--mirror below--#'
                mirror_automod = mirror_automod.split(split_string)[0] + split_string
                
                r.edit_wiki_page(mirror,'config/automoderator',mirror_automod+source_automod)

                automod_updated = True
            
            

            #keep track of what we've done
            data['modlog'].append(entry.id)
    
    def auth(self):
        #Replace this with OAuth shenanigans once it stops being broken
        r.login('wpd_de',os.environ.get('password'))
    
    def run(self):
        
        self.login()
        while True():
            self.mirror_new()
            self.mirror_mod()
            self.save_cache()
            time.sleep(30)
            
            

            
        
