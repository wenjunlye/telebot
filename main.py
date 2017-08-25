import StringIO
import json
import logging
import random
import urllib
import urllib2
import time
import datetime
import math
import copy

import secrets

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = secrets.token

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'

classID = secrets.class_id
meID = secrets.class_id

class SG(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=8)
    def tzname(self, dt):
        return "SGT"
    def dst(self, dt):
        return datetime.timedelta(hours=8)

sg = SG()

timetable_original = [
    ['/oddmonday',     'CLC, Humans, LA\nIM, Chem'],
    ['/oddtuesday',    'Bio, HCL, PE\nLA, Chem(lab)'],
    ['/oddwednesday',  'IM, LA, Humans\nIH, CCE'],
    ['/oddthursday',   'IM, PE, HCL\nHumans, LA'],
    ['/oddfriday',     'IH, Bio(lab), IM\nHCL, Chem, LA'],
    ['/evenmonday',    'HCL, PE\nIM'],
    ['/eventuesday',   'HCL, LA, Bio(lab)\nHumans, Chem(lab)'],
    ['/evenwednesday', 'Humans, IH, IM\nLA, CCE'],
    ['/eventhursday',  'PE, LA, Bio\nIM, Assembly'],
    ['/evenfriday',    'IH, LA, Bio\nChem, IM, HCL']
]

timetable = copy.deepcopy(timetable_original)

imgs = [
    'http://bi.gazeta.pl/im/36/19/14/z21076790IER,23-mlode-pandy-urodzone-w-tym-roku-w-centrum-badaw.jpg',
    'https://i2.wp.com/travelwirenews.com/wp-content/uploads/2017/04/217.218.67.2336f0c9d77-1c7e-4a96-b532-d-9d343bc91aadb5dd309a79d9165c4009980bc5fb.jpg?fit=650%2C366',
    'http://abcnews.go.com/images/Lifestyle/rtr_baby_pandas_07_jc_160930.jpg',
    'https://www.icetrend.com/wp-content/uploads/2016/10/gty_baby_pandas_01_jc_160930_4x3_992.jpg',
    'https://lh3.googleusercontent.com/-CG5d421qQFg/Vmql2Ygit9I/AAAAAAAAAiY/Drr0kh7BeWM/w1100-h734/2.jpg',
    'https://pbs.twimg.com/profile_images/494064548035719168/U8cDoHB-.jpeg',
    'http://www.watson.ch/imgdb/57ab/Qtablet_hq,E,0,0,700,700,291,291,116,116/5221191888988022',
    'https://media1.popsugar-assets.com/files/thumbor/rTkEeGRG84fNJLov7m_xMHy6tBs/fit-in/2048xorig/filters:format_auto-!!-:strip_icc-!!-/2012/09/39/4/192/1922243/cf3f7dcec6701811_cute_pomeranians_main/i/Cute-Pomeranian-Pictures.jpg',
    'http://www.accessonslow.com/images/animed%20kitten%20001.jpg',
    'http://www.ordissinaute.fr/sites/default/files/styles/diaporama_slide/public/diaporama_images/chaton-endormi-dans-tasse-rayures-bleues-blanches-r-default.jpg?itok=P7htWAdy',
    'https://cdn.quizme.se/quiz/f709bd27-a278-4591-b9bf-d6e43bec873a.PNG',
    'http://www.mrwallpaper.com/wallpapers/Cute-Puppy-Kitten.jpg',
    'https://static.curazy.com/wp-content/uploads/2015/02/1452522_6.jpg',
    'http://data.whicdn.com/images/233453379/original.jpg',
    'http://www.minimaltese.com.au/images/image003%20(1).jpg',
    'http://hyperanzeigen.at/x-at/inz/340/340931-zwei-sch-F6ne-m-E4nnliche-und-weibliche-malteser-welpen-1.jpg',
    'https://effe7b274fb7be1907a5-260e1b894ca23dd8bee041f5045ecd74.ssl.cf1.rackcdn.com/img-45-591965-original-59088daea8b08.jpg',
    'http://images.locanto.sg/1974694362/Mini-maltese-puppy-for-sale-sold_3.jpg',
    'http://pm1.narvii.com/6125/610e60d75ed8df775754e285948649245c5381b9_hq.jpg',
    'https://i0.wp.com/doglers.com/wp-content/uploads/2016/02/Alaskan-Malamute-Puppy-Photo.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/273-lonely-soda_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/published/271a-babynoteeth.jpg?1495692681',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/270-zaihuni_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/265-bee-and-calendar1_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/265-bee-and-calendar2_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/expressway_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/260_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/241-strawberry-cake_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/chocolate-cake_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/230-da-bao_1_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/233-chashaobao_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/234-dou-sha-bao_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/xiao-long-bao_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/han-bao-bao_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/totogod_orig.jpg',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/published/2tyred.jpg?1500999622',
    'http://www.bitterstickgirl.sg/uploads/2/4/9/0/24906893/published/275-dmj.jpg?1498403610'
]

gifs = [
    'http://31.media.tumblr.com/tumblr_m80f4bhmeY1rq5rj4o1_500.gif',
    'https://omfgdogs.com/omfgdogs@2X.gif',
    'http://bestanimations.com/Animals/Mammals/Cats/cats/cute-kitty-animated-gif-25.gif',
    'https://media.giphy.com/media/100QWMdxQJzQC4/giphy.gif',
    'https://s-media-cache-ak0.pinimg.com/originals/cd/22/85/cd228571a7ec2d8d542eb89b626709e2.gif'
    'https://media.giphy.com/media/SF8qWBUl4sV7G/giphy.gif',
    'http://thefw.com/files/2013/03/Cute-Cat.gif',
    'http://www.pbh2.com/wordpress/wp-content/uploads/2014/08/floppy-kitten.gif',
    'https://media.tenor.com/images/829f6074248e6c6437ef9986bce57575/tenor.gif',
    'https://media.tenor.com/images/2d512f1f6ef6b260d94acb429d3e794c/tenor.gif',
    'https://media.tenor.com/images/a7bd6b94430c1e66148d580209e377c5/tenor.gif',
    'https://media.giphy.com/media/3oEdv4hwWTzBhWvaU0/giphy.gif',
    'http://data.whicdn.com/images/201782005/original.gif',
    'https://media.tenor.com/images/035f033ebba7fae7019e543a81a81233/tenor.gif'
]

# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

class Commands(ndb.Model):
    # key name: str(sender)
    command = ndb.StringProperty()
    argDate = ndb.DateProperty()
    argText = ndb.StringProperty()
    
class Humanities(ndb.Model):
    # key name: str(sender)
    humans = ndb.StringProperty()
    
class Things(ndb.Model):
    # key name: hw_id
    duedate = ndb.DateProperty()
    thing = ndb.StringProperty()

class Birthdays(ndb.Model):
    # key name: bday_id
    birthday = ndb.DateProperty()
    name = ndb.StringProperty()

# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

def updateCommand(sender, command, argDate, argText):
    c = Commands.get_or_insert(str(sender))
    if command != '':
        c.command = command
    if argDate != datetime.datetime.min:
        c.argDate = argDate
    if argText != '':
        c.argText = argText
    c.put()

def clearCommand(sender):
    c = Commands.get_or_insert(str(sender))
    c.command = ''
    c.argDate = datetime.datetime.min
    c.argText = ''
    c.put()
    
def getCommand(sender):
    c = Commands.get_by_id(str(sender))
    if c:
        command = c.command
        argDate = c.argDate
        argText = c.argText
    return command, argDate, argText

def setHumans(sender, subj):
    h = Humanities.get_or_insert(str(sender))
    h.humans = subj
    h.put()
    
def getHumans(sender):
    h = Humanities.get_by_id(str(sender))
    if h:
        return h.humans
    return 'Humans'

def addThing(hw_id, date, name):
    t = Things.get_or_insert(hw_id)
    t.duedate = date
    t.thing = name
    t.put()
    
# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        try:
            message = body['message']
        except:
            message = body['edited_message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id'] # unique identifier of chat
        sender = fr['id'] # unique identifier of sender

        if not text:
            logging.info('no text')
            return

        # KEYBOARDS AND REPLYING
        removekb = json.dumps({'remove_keyboard': True,
                               'selective': True})
        forcereply = json.dumps({'force_reply': True,
                                'selective': True})
        def reply(msg=None, img=None, gif=None, keyboard=removekb, debug=False):
            if msg:
                if debug:
                    recipient = meID
                    reply = ''
                else:
                    recipient = str(chat_id)
                    reply = str(message_id)
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': recipient,
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': reply,
                    'reply_markup': keyboard
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
                action = resp = urllib2.urlopen(BASE_URL + 'sendChatAction', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'action': 'upload_photo'
                })).read()
            elif gif: 
                resp = multipart.post_multipart(BASE_URL + 'sendDocument', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('document', 'gif.gif', gif),
                ])
                action = resp = urllib2.urlopen(BASE_URL + 'sendChatAction', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'action': 'upload_document'
                })).read()
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        # TIMETABLE CALCULATIONS
        nextschday = [1, 2, 3, 4, 5, 0, 0, 6, 7, 8, 9, 0, 5, 5]
        now = datetime.datetime.now(sg)
        startterm = datetime.datetime(2017, 6, 24, 0, 0, 0, tzinfo=sg)
        delta = now - startterm
        split = str.split(str(delta))
        week = math.floor(int(split[0])/7 + 1)
        if week > 10:
            week = 0
        dayofweek = now.weekday()
        
        humans = getHumans(sender)
        for i in range(0, len(timetable)-1):
            timetable[i][1] = timetable_original[i][1].replace("Humans", humans)
        
        allhw = []
        query = Things.query(Things.duedate > now).order(Things.duedate)
        
        # ENABLING AND DISABLING
        if text.startswith('/'):
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
                
        def checkCommand(command, date, arg):
            complete = True
            
            # INCOMPLETE COMMANDS
            if command == '/addhomework':
                if date == datetime.datetime.min:
                    reply("When is this homework due?", keyboard=forcereply)
                    complete = False
                elif arg == '':
                    reply("What is the homework called?", keyboard=forcereply)
                    complete = False
            elif command == '/delhomework':
                if arg == '':
                    for q in query:
                        allhw.append(["%s %s" % (q.duedate.strftime("%d/%m"), q.thing)])
                    hwkeyboard = json.dumps({'keyboard': allhw, 
                                                'one_time_keyboard': True, 
                                                'resize_keyboard': True,
                                                'selective': True})
                    reply("Which homework would you like to delete?", keyboard=hwkeyboard)
                    complete = False
            elif command == '/sethumans':
                if arg == '':
                    reply("What would you like your humanities subject to show as?", keyboard=forcereply)
                    complete = False
            elif command == '/next':
                if arg == '':
                    reply("What subject do you want to search for?", keyboard=forcereply)
                    complete = False
            if complete == False:
                updateCommand(sender, command, date, arg)
            
            return complete
            
        if getEnabled(chat_id):
            # CONTINUATION OF INCOMPLETE COMMANDS
            if 'reply_to_message' in message and 'username' in message['reply_to_message']['from']:
                if message['reply_to_message']['from']['username'] == 'threeoheight_bot':
                    # check the context of the incomplete command
                    incomplete = getCommand(sender)
                    command = incomplete[0]
                    date = incomplete[1]
                    arg = incomplete[2]
                    
                    
                    if command == '/sethumans' or command == '/next':
                        if arg == '':
                            arg = text
                        complete = checkCommand(command, date, arg)
                        if complete:
                            text = "%s %s" % (command, arg)
                    elif command == '/addhomework':
                        if date < datetime.date(1991, 1, 1):
                            date = datetime.datetime.strptime(text+'/2017', "%d/%m/%Y")
                        elif arg == '':
                            arg = text
                        
                        complete = checkCommand(command, date, arg)
                        if complete:
                            text = "%s %s %s" % (command, datetime.datetime.strftime(date, "%d/%m"), arg)
                    elif command == '/delhomework':
                        query = Things.query(Things.thing == text[6:])
                        for q in query:
                            print(q.key.id())
                            target = q.key
                            target.delete()
                            reply("Ok, %s has been deleted." % text)
            if text.startswith('/'):
                text = str(text).replace('@threeoheight_bot', '')
                splitCommand = str.split(text)

                command = splitCommand[0]
                date = datetime.datetime.min
                arg = ''

                try:
                    date = datetime.datetime.strptime(splitCommand[1]+'/2017', "%d/%m/%Y")
                except:
                    arg = ' '.join(splitCommand[1:])
                else:
                    arg = ' '.join(splitCommand[2:])
                    
                complete = checkCommand(command, date, arg)
                
                # COMPLETE COMMANDS
                if complete:
                    if arg == '/cancel' or command == '/cancel':
                        clearCommand(sender)
                        reply("Command cancelled")
                    
                    # TIMETABLE
                    elif command == '/tomorrow':
                        index = dayofweek
                        if week % 2 == 0: #even week
                            index += 7
                        index = nextschday[index]
                        reply("%s:\n%s" % (timetable[index][0], timetable[index][1]))

                    elif command == '/weekno':
                        if dayofweek <= 4:
                            reply("This week is week %d" % week)
                        else:
                            reply("Next week is week %d" % week)

                    elif command == '/next':
                        subj = arg
                        index = dayofweek
                        if week % 2 == 0: #even week
                            index += 7
                        index = nextschday[index]
                        start = index

                        while True:
                            if subj in timetable[index][1]:
                                oddity = week % 2
                                if 'odd' in timetable[index][0]:
                                    oddity2 = 1
                                else:
                                    oddity2 = 0

                                weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                                day = weekdays[index%5]
                                diff = index%5 - dayofweek

                                if oddity == oddity2:
                                    thisnext = 'this'
                                    if diff < 0:
                                        thisnext = 'next next'
                                        diff += 14
                                else:
                                    thisnext = 'next'
                                    diff += 7
                                d = now + datetime.timedelta(diff)

                                reply("The next %s lesson is %s %s, %d/%d (%s)" % (subj, thisnext, day, d.day, d.month, timetable[index][0]))
                                break
                            else:
                                index = (index + 1) % 10

                            if index == start:
                                reply("Subject not found.")
                                break
                    elif command == '/sethumans':
                        setHumans(sender, arg)
                        reply("Humanities subject for %s has been set to %s" % (fr['first_name'], getHumans(sender)))
                    
                    # HOMEWORK
                    elif command == '/addhomework':
                        addThing(time.strftime("%d%m%Y%I%M%S"), date, arg)
                        reply("Ok, %s has been set." % arg)
                    elif command == '/gethomework' or command == '/thisweek':
                        if command == '/thisweek':
                            query = query.filter(Things.duedate < now + datetime.timedelta(days=7))

                        response = ""
                        for q in query:
                            response = response + q.duedate.strftime("%d/%m")+' '+q.thing + '\n'

                        if response == "":
                            reply("There's no homework! Rejoice!")
                        else:
                            reply(response)

                    # BIRTHDAYS
                    elif command == '/nextbirthday':
                        # really roundabout way of doing this but i don't know how else to do this
                        query = Birthdays.query(Birthdays.birthday > now).order(-Birthdays.birthday)
                        for q in query:
                            response = "%s %s" % (q.birthday.strftime('%d/%m'), q.name)
                        reply(response)
                        
                    # MISCELLANEOUS
                    elif command == '/cute':
                        imgvsgif = random.randint(0,1)
                        if imgvsgif == 0: #img
                            url = imgs[random.randint(0, len(imgs)-1)]
                            reply(img=urllib2.urlopen(url).read())
                        else:
                            url = gifs[random.randint(0, len(gifs)-1)]
                            reply(gif=urllib2.urlopen(url).read())
                    else:
                        for day in timetable:
                            if day[0] in text:
                                reply(day[1])
                    
                    clearCommand(sender)

class CustomMessage(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        msg = self.request.get('msg')
        chat = self.request.get('chat')
        resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
            'chat_id': str(chat) or meID,
            'text': msg,
            'parse_mode': 'Markdown'
        })).read()
        
class CheckBday(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        nowtime = datetime.datetime.now()
        thism = nowtime.month
        thisd = nowtime.day
        query = Birthdays.query(Birthdays.birthday == datetime.date(2017, thism, thisd))
        for q in query:
            resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                'chat_id': classID,
                'text': "Happy birthday %s!" % q.name
            })).read()
            
class CheckTimetable(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        
        now = datetime.datetime.now(sg)
        startterm = datetime.datetime(2017, 6, 24, 0, 0, 0, tzinfo=sg)
        delta = now - startterm
        split = str.split(str(delta))
        week = math.floor(int(split[0])/7 + 1)
        if week > 10:
            week = 0
        dayofweek = now.weekday()
        
        tmr = (dayofweek + 1)%7
        if tmr <= 4: # if tomorrow is a weekday
            index = tmr
            if week % 2 == 0: # even week
                index += 5
            ttb = timetable[index]
            triggers = ['PE']
            
            for trigger in triggers:
                if trigger in ttb[1]:
                    resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                        'chat_id':  classID,
                        'text': "There's %s tomorrow! (%s)" % (trigger, ttb[0]),
                        'parse_mode': 'Markdown'
                    })).read()
                    

app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
    ('/msg', CustomMessage),
    ('/checkbday', CheckBday),
    ('/checkttb', CheckTimetable)
], debug=True)