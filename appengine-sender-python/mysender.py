#!/usr/bin/env python

import os
import time
import cloudstorage as gcs
import webapp2
import urllib
import base64
from uuid import uuid1
from google.appengine.ext import ndb
from google.appengine.api import app_identity
from google.appengine.api import mail

TOKEN = '<RETRIEVE FROM DATASTORE>'
BUCKET = '<RETRIEVE FROM DATASTORE>'
SENDER = '<RETRIEVE FROM DATASTORE>'

MY_DEFAULT_RETRY_PARAMS = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(MY_DEFAULT_RETRY_PARAMS)

class SenderSettings(ndb.Model):
  name = ndb.StringProperty()
  value = ndb.StringProperty()

  @staticmethod
  def get(name):
    NOT_SET_VALUE = "NOT SET"
    retval = SenderSettings.query(SenderSettings.name == name).get()
    if not retval:
      retval = SenderSettings()
      retval.name = name
      retval.value = NOT_SET_VALUE
      retval.put()
    return retval.value

class ObjectIndex(ndb.Model):
    name = ndb.StringProperty()
    email = ndb.StringProperty()
    gs = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

class Upload(webapp2.RequestHandler):
    def post(self):
        self.configure()

        if TOKEN != self.request.get('token'):
          self.response.out.write('Wrong token!')
          return

        filename = self.request.get('filename')
        gs_path = "/{}/{}/{}".format(BUCKET, uuid1().hex[:20], filename)

        self.update_datastore(gs_path)

        self.update_storage(gs_path)

        self.email(SENDER, self.request.get('email'), filename, self.get_url(gs_path))

    def configure(self):
        global TOKEN, BUCKET, SENDER
        TOKEN = SenderSettings.get('TOKEN')
        BUCKET = SenderSettings.get('BUCKET')
        SENDER = SenderSettings.get('SENDER')

    def update_datastore(self, gs_path):
        storedobject = ObjectIndex()
	storedobject.name = self.request.get('filename')
	storedobject.gs = gs_path
        storedobject.email = self.request.get('email')
        storedobject.put()

    def update_storage(self, gs_path):
        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        gcs_file = gcs.open(gs_path,
                            'w',
                            content_type='binary/octet-stream',
                            retry_params=write_retry_params)
        gcs_file.write(self.request.get('content'))
        gcs_file.close()

    def get_url(self, path):
        expire_time = int(time.time()) + 86400
        message = '\n'.join([
            'GET',
            '',
            '',
            str(expire_time),
            path
        ])
        signing_key_name, signature = app_identity.sign_blob(message)

        query_params = {
            'GoogleAccessId': app_identity.get_service_account_name(),
            'Expires': str(expire_time),
            'Signature': base64.b64encode(signature)
        }

        return 'https://storage.googleapis.com' + path + '?' + urllib.urlencode(query_params)

    def email(self, sender, recepient, filename, url):
        mail.send_mail(sender=sender,
            to=recepient,
            subject="Linke to the uploaded file",
            body="""Dear {}

Please use link below for download {}
{}

The App Engine App
""".format(recepient, filename, url))

application = webapp2.WSGIApplication([
    ('/upload', Upload),
], debug=True)
