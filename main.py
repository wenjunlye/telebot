import StringIO
import json
import logging
import random
import urllib
import urllib2

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


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)


class Commands(ndb.Model):
    # key name: str(sender)
    command = ndb.StringProperty()
    argDate = ndb.DateProperty()
    argText = ndb.StringProperty()
    
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
        chat_id = chat['id']

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

        def checkCommand(command, date, arg):
            complete = True
            
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
                    
            if text.startswith('/'):
                text = str(text).replace('@threeoheight_bot', '')
                splitCommand = str.split(text)
                # TODO: account for commands that don't start from the 0th character, e.g. 'and /cute'

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


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
