import praw
import json
from collections import deque
from collections import OrderedDict

###   CONFIGS   ###

#praw
r=praw.Reddit('Subreddit mirror bot')

#Subreddit to scrape
source = r.get_subreddit('')

#Subreddit to act as mirror
mirror = r.get_subreddit('')

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

    def mirror_new(self):
        #Check /new for any submissions and mirror them.\
        #Record the id pairings
        for submission in source.get_new(limit=100):

            #avoid duplicate posts
            if submission.fullname in data['mappings']:
                continue

            self.mirror_submission(submission)


    def mirror_mod(self):

        #Keep a temporary list of things that have already been acted on this cycle.
        #This ensures that in the case of multiple approve/remove, only the most recent action is mirrored
        items_acted_on = []
        users_acted_on = []
        
        #Check /about/modlog and mirror actions as needed
        for entry in source.get_mod_log(limit=100):

            #ignore most actions
            if entry.action not in ['approvelink','removelink','banuser','unbanuser']:
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

            #keep track of what we've done
            data['modlog'].append(entry.id)

            #begin mirroring process
            if entry.action in ['approvelink','removelink']:

                #avoid conflicting actions
                items_acted_on.append(entry.target_fullname)

                #Find corresponding mirror post
                #If none, continue
                if entry.target_fullname not in data['mappings']:
                    
                    continue

                mirror_post = r.get_info(data['mappings'][entry.target_fullname])

                if entry.action == 'approvelink':
                    mirror_post.approve()
                if entry.action == 'removelink':
                    mirror_post.remove()
                
                
            elif entry.action in ['banuser','unbanuser']:
                users_acted_on.append(entry.target_author)
