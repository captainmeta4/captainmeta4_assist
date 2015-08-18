import praw
import time
import os
import random

r=praw.Reddit("Markov user simulator bot by /u/captainmeta4")

###Configs

#userlist
userlist = [
    'chooter',
    'Deimorz'
    ]

subreddit = r.get_subreddit('AdminSimulator')

#oauth stuff
client_id = os.environ.get('client_id')
client_secret = os.environ.get('client_secret')
r.set_oauth_app_info(client_id,client_secret,'http://127.0.0.1:65010/authorize_callback')

###End Configs

class Bot():

    def auth(self, keyname):
        #r.refresh_access_information(os.environ.get(keyname))
        r.login(keyname,os.environ.get('password'))

    def text_to_triples(self, text):
        #generates triples given text

        data = text.split()

        #cancel out on comments that are too short
        if len(data) < 3:
            return

        self.lengths.append(len(data))

        #iterate through triples
        for i in range(len(data)-2):
            yield (data[i], data[i+1], data[i+2])

    def text_to_tuples(self, text):
        #generates tuples given text

        data = text.split()

        #cancel out on comments that are too short
        if len(data) < 2:
            return

        #iterate through triples
        for i in range(len(data)-1):
            yield (data[i], data[i+1])
        

    def generate_corpus(self, user):

        print("generating corpus for /u/"+str(user)+"...")
        #loads comments and generates a dictionary of
        #  {('word1','word2'): ['word3','word4','word5'...]...}

        self.corpus = {}
        self.starters = []
        self.lengths = []
        
        #for every comment
        for comment in user.get_comments(limit=1000):

            #ignore mod comments
            if comment.distinguished == "moderator":
                continue

            #ignore /r/spam comments
            if str(comment.subreddit) == "spam":
                continue
            
            #print("processing comment "+str(i))
            #get 3-word sets
            #add comment starters to starters list
            start_of_comment=True
            
            for triple in self.text_to_triples(comment.body):
                key = (triple[0], triple[1])

                #note valid comment starters
                if start_of_comment:
                    self.starters.append(key)
                    start_of_comment=False

                #add to corpus

                if key in self.corpus:
                    self.corpus[key].append(triple[2])
                else:
                    self.corpus[key] = [triple[2]]
        print("...done")
        print("Corpus for /u/"+str(user)+" is "+str(len(self.corpus))+" entries")
        

    def generate_text(self, text=""):
        key = self.create_starter(text)
        sentence = self.continue_text(key)
        return sentence

    def continue_text(self, key):

        #start the output based on a key of ('word1','word2)
        output = key[0]+" "+key[1]

        #Add words until we hit text-ending criteria or a key not in the corpus
        while True:

            if (len(output.split())> length and
                ((output.endswith(".") and not output.endswith("..."))
                 or output.endswith("!")
                 or output.endswith("?"))
                ):
                break

            if key not in self.corpus:
                break
            
            next_word = random.choice(self.corpus[key])
            output += " " + next_word

            key = (key[1], next_word)
        return(output)

    def create_starter(self, text):
        #get tuples of a phrase and return a hit for starters

        possible_starters=[]
        for key in self.text_to_tuples(text):
            if key in self.starters:
                possible_starters.append(key)
        
        #if there are any matches, go with it, otherwise choose random starter
        if len(possible_starters) > 0:
            return random.choice(possible_starters)
        else:
            return random.choice(self.starters)
        
    def get_random_comment(self, x):
        #returns a random comment within the newest X

        #reset x to random
        x=random.randint(1,x)

        #get the x'th post and return it
        for comment in subreddit.get_comments(limit=x):
            post = comment
            
        return post

    def run_cycle(self):
        
        #pick a random admin
        username = random.choice(userlist)
        
        #auth as correspondign sim bot
        self.auth(username)
        
        user=r.get_redditor(username)
        self.generate_corpus(user)
        
        try:
            text = self.generate_text
            print(comment)
        except:
            return
            
        #x% chance of making this as a new post
        #y% chance of making a top-level comment on existing post
        #z% chance of making a child comment
        i = random.randint(1,100)
        
        if i<=100:
            #title is first sentence
            title = re.split("(?<=[.?!]) ",text,maxsplit=1)[0]
            r.submit(subreddit,title,text=text)
            
        
        
    def run(self):
        
        while True:
            self.run_cycle()
            time.sleep(60*10)

            

if __name__=="__main__":
    bot=Bot()
    bot.run()
