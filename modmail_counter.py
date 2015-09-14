import praw
import time
r=praw.Reddit('modmail counter by captainmeta4')

##CONFIGS

username = 'captainmeta4'
subreddit = r.get_subreddit('gadgets')

begin_time = "01 Aug 2015 00:00:00"
end_time = "31 Aug 2015 23:59:59"

r.login(username,input('password: '), disable_warning = True)

##END CONFIGS


#generator to return all message replies
#yay recursion
def all_replies(message):
    yield message
    for reply in message.replies:
        for child in all_replies(reply):
            yield child

#convert times to timestamps
begin_time = time.strptime(begin_time, "%d %b %Y %H:%M:%S")
end_time = time.strptime(end_time, "%d %b %Y %H:%M:%S")

begin_time = time.mktime(begin_time)
end_time = time.mktime(end_time)
print(begin_time)
print(end_time)

#pre-load all current polmods
first_response = {}
total_response = {}
for mod in r.get_moderators(subreddit):
    first_response[str(mod)]=0
    total_response[str(mod)]=0

for modmail in r.get_mod_mail(subreddit, limit=5000):

    #ignore mod-created threads
    if modmail.distinguished is not None:
        continue

    #check thread creation time - August 2015
    if (modmail.created_utc < begin_time or
        modmail.created_utc > end_time):
        continue
    
    #keep track of first responder
    first_responder = True

    #keep track of who has points so far this thread
    thread_scored = []
    
    for reply in all_replies(modmail):

        #set last bumped
        last_bumped = reply.created_utc

        #ignore non-mod replies
        if reply.distinguished is None:
            continue

        #ignore replies whose authors already have points this thread
        if str(reply.author) in thread_scored:
            continue
        thread_scored.append(str(reply.author))

        #check first responder; award point
        if first_responder == True:
            try:
                first_response[str(reply.author)] += 1
            except KeyError:
                first_response[str(reply.author)] = 1
            
        first_responder = False

        #award participation point
        try:
            total_response[str(reply.author)] += 1
        except KeyError:
            total_response[str(reply.author)] = 1

print('##Participation in user-initiated threads')
print('')
print('Mod|First Response|Total Participation')
print('-|-|-')
for entry in total_response:

    if entry in first_response:
        score = {'name':entry, 'first':first_response[entry], 'total':total_response[entry]}
    elif entry not in first_response:
        score = {'name':entry, 'first':0, 'total':total_response[entry]}

    print("%(name)s | %(first)s | %(total)s" % score)
    
