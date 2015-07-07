#This is a script that can be run in order to generate false submissions on /r/undelete
#This script exists for the sole purpose of assholery.

import praw
import time

r.login(input("Username: "), input("Password: "))

#Get a list of subs that the user moderates
my_moderation=[]
for subreddit in r.get_my_moderation(limit=1000):
    my_moderation.append(subreddit.display_name)
    
#Load the top 1000 submissions from /r/all/hot and make a listing of submissions that I can remove
posts = []
for submission in r.get_subreddit('all').get_hot(limit=1000):
    if submission.subreddit.display_name in my_moderation:
        posts.append(submission.fullname)
        
print("Found "+str(len(posts))+" usable submissions")
print("Removing posts...")

Remove all the posts
for submission in r.get_info(thing_id=posts):
    submission.remove()

print("posts removed")
print("Waiting 30 seconds")

time.sleep(30)

print("Restoring posts...")
for submission in r.get_info(thing_id=posts):
    submission.remove()

print("posts restored")
