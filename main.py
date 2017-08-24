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

        if text.startswith('/'):
            if text == '/start':
                reply('Bot enabled')
                setEnabled(chat_id, True)
            elif text == '/stop':
                reply('Bot disabled')
                setEnabled(chat_id, False)
        
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
            timetable[i][1] = timetableORG[i][1].replace("Humans", humans)
        
        allhw = []
        query = Things.query(Things.duedate > now).order(Things.duedate)
        
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
                                if oddity == oddity2:
                                    thisnext = 'this'
                                else:
                                    thisnext = 'next'

                                weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                                day = weekdays[index%5]
                                diff = index%5 - dayofweek

                                if index%5 < dayofweek:
                                    diff += 7
                                if thisnext == 'next':
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
                    
                    # BIRTHDAYS
                    elif command == '/nextbirthday':
                        # really roundabout way of doing this but i don't know how else to do this
                        query = Birthdays.query(Birthdays.birthday > now).order(-Birthdays.birthday)
                        for q in query:
                            response = "%s %s" % (q.birthday.strftime('%d/%m'), q.name)
                        reply(response)
                        
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