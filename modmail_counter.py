import praw
import time

##CONFIGS

username = 'captainmeta4'
subreddit = input('subreddit: /r/')

print('Input dates in format 01 Jan 2016')
begin_day = input('Begin Day: ')
end_day = input('End Day: ')



begin_time = begin_day+" 00:00:00"
end_time = end_day+" 23:59:59"

##END CONFIGS

#instanciate reddit and log in
r=praw.Reddit('modmail counter by /u/captainmeta4, running under /u/'+username)
r.login(username,input('password: '), disable_warning = True)

#turn subreddit name into subreddit object
subreddit = r.get_subreddit(subreddit)

#generator to return all message replies
#yay recursion
def all_replies(message):
    yield message
    for reply in message.replies:
        for child in all_replies(reply):
            yield child

#convert times to timestamps
##step 1 - parse strings to strftime objects
begin_time = time.strptime(begin_time, "%d %b %Y %H:%M:%S")
end_time = time.strptime(end_time, "%d %b %Y %H:%M:%S")

##step 2 - turn strftime objects into epoch timestamps
begin_time = time.mktime(begin_time)
end_time = time.mktime(end_time)

#pre-load all current mods from modlist
first_response = {}
total_response = {}
for mod in r.get_moderators(subreddit):
    first_response[mod.name]=0
    total_response[mod.name]=0

#load modmails
for modmail in r.get_mod_mail(subreddit, limit=5000):

    #ignore mod-created or admin-created threads
    if modmail.distinguished is not None:
        continue

    #check thread creation time - continue if thread too recent
    #not worrying about thread too old just yet
    if modmail.created_utc > end_time:
        continue

    #keep track of last-bumped time
    last_bumped = modmail.created_utc
    
    #keep track of first responder
    first_responder = True

    #keep track of who has points so far this thread
    thread_scored = []
    
    for reply in all_replies(modmail):

        #update last_bumped
        if reply.created_utc > last_bumped:
            last_bumped = reply.created_utc

        #check thread creation time again; skip over if too old
        #this is checked here (instead of above) so that we can get an accurate last_bumped
        if modmail.created_utc < begin_time:
            continue

        #ignore non-mod replies
        if reply.distinguished is None:
            continue

        #ignore replies whose authors already have points this thread
        if reply.author.name in thread_scored:
            continue
        thread_scored.append(reply.author.name)

        #check first responder; award point
        if first_responder == True:
            try:
                first_response[reply.author.name] += 1
            except KeyError:
                first_response[reply.author.name] = 1
            
        first_responder = False

        #award participation point
        try:
            total_response[reply.author.name] += 1
        except KeyError:
            total_response[reply.author.name] = 1

    #check last bumped - this will be an accurate termination criteria
    if last_bumped < begin_time:
        break

#sort by first_response - modlist will contain the mod sort order
modlist = []
for entry in first_response:
    i=0
    for mod in modlist:
        if first_response[entry] < first_response[mod]:
            i+=1
        else:
            break
    modlist.insert(i,entry)
    
print('##Participation in user-initiated modmail threads')
print('')
print('Mod|First Response|Total Participation')
print('-|-|-')

#now iterate through the sorted modlist to output the copy-pasteable text
for entry in modlist:

    if entry in first_response:
        score = {'name':entry, 'first':first_response[entry], 'total':total_response[entry]}
    elif entry not in first_response:
        score = {'name':entry, 'first':0, 'total':total_response[entry]}

    print("%(name)s | %(first)s | %(total)s" % score)
    
