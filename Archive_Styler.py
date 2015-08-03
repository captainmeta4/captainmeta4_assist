#script to set up new archives and deploy new settings
import praw
import json
import os

r=praw.Reddit("modmail archive styling sync by captainmeta4")

r.login("modmail_archivist",os.environ.get("password"))

#get stylesheet
stylesheet = r.get_wiki_page("cm4bots_modmail","config/stylesheet").content_md

#get sidebar
sidebar = r.get_wiki_page("cm4bots_modmail","config/sidebar").content_md

#get automod
automod = r.get_wiki_page("cm4bots_modmail","config/automoderator").content_md

#get subreddit listings
mappings = json.loads(r.get_wiki_page("captainmeta4bots","archivist").content_md)

#for mapping in mappings:
archive = "futurology_modmail"
#set stylesheet
r.set_stylesheet(archive, stylesheet)
#set sidebar
r.update_settings(r.get_subreddit(archive), domain_sidebar=sidebar)
#set automod
r.edit_wiki_page(archive, "config/automoderator", automod)
