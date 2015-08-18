import praw
import time
import os
import random

r=praw.Reddit("Markov user analysis bot")

###Configs

#oauth stuff
#client_id = os.environ.get('client_id')
#client_secret = os.environ.get('client_secret')
#r.set_oauth_app_info(client_id,client_secret,'http://127.0.0.1:65010/authorize_callback')

user2=[]

###End Configs

class Bot():

    def auth(self):
        #r.refresh_access_information(os.environ.get(refresh_token))
        r.login('captainmeta4',input('password: '))

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
        

    def generate_sentence(self, text=""):
        key = self.create_starter(text)
        sentence = self.continue_sentence(key)
        return sentence


    def continue_sentence(self, key):

        #start the output based on a key of ('word1','word2)
        output = key[0]+" "+key[1]

        #Add words until we hit a sentance-ender or a key not in the corpus
        while not ((output.endswith(".") and not output.endswith("..."))
                   or output.endswith("!")
                   or output.endswith("?")):

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
        
    def generate_text(self, text=""):
        length = random.choice(self.lengths)

        output = self.generate_sentence(text)

        while len(output.split())<length:
            output += " " + self.generate_sentence(text)

        return output

    def run_cycle(self):
        
        user2=""

        while True:

            username = input('user: ')
            
            if username != user2:
                user=r.get_redditor(username)
                self.generate_corpus(user)
                user2=username
            try:
                comment = ("/u/"+str(user)+
                           "\n\n* "+self.generate_text()+
                           "\n\n* "+self.generate_text()+
                           "\n\n* "+self.generate_text()
                           )
                print(comment)
            except:
                pass
        
        
    def run(self):
        
        #self.auth()
        
        self.run_cycle()

            

if __name__=="__main__":
    bot=Bot()
    bot.run()
