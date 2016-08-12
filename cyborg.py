import praw
import os
import re
import functools

r=praw.Reddit('personal nuke command')
ME = 'captainmeta4'

class Bot():
    def __init__(self):
        self.commands={
            "nuke":functools.partial(self.nuke),
            "ban":functools.partial(self.ban)
            }

    def login(self):

        r.login(ME,os.environ.get('password'), disable_warning=True)

    def ban(self, comment):
        parent_comment = r.get_info(thing_id=comment.parent_id)
        
        redditor = parent_comment.author
        subreddit = comment.subreddit
        subreddit.add_ban(redditor)

    def nuke(self, comment):
        self.remove_recursively(r.get_info(thing_id=comment.parent_id))

    def remove_recursively(self, comment):

        print('removing: '+comment.body)
        comment.remove()

        comment.refresh()
        for reply in comment.replies:
            self.remove_recursively(reply)

    def mainloop(self, ):

        self.login()

        for comment in praw.helpers.comment_stream(r, "mod", limit=100, verbosity=0):

            #ignore comments without authors (deleted users)
            if comment.author is None:
                continue
            
            #ignore comments not by me
            if comment.author.name != ME:
                continue

            #ignore comments not starting with !
            if comment.body.startswith("!"):
                command = re.match("!(\w+)",comment.body).group(1)

                #check if valid command
                if command not in self.commands:
                    comment.edit(comment.body+"\n\n*command not found*")
                    comment.remove()
                    continue

                #command exists; retrieve parent comment and execute

                comment.remove()
                self.commands[command](comment)
                


if __name__=="__main__":
    bot=Bot()
    bot.mainloop()
                
        

                
