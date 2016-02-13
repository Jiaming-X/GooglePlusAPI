import json
import flask
import httplib2
import logging

from apiclient import errors
from apiclient import discovery
from oauth2client import client
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from apiclient.discovery import build
from oauth2client.client import OAuth2WebServerFlow


logging.basicConfig()
app = flask.Flask(__name__)

## TODO: register in console.developers.google.com, and fill these variables
client_id = ''
client_secret = ''
redirect_uri = ''
scope='https://www.googleapis.com/auth/plus.login'

@app.route('/')
def index():
  if 'credentials' not in flask.session:
    return flask.redirect(flask.url_for('oauth2callback'))
  credentials = client.OAuth2Credentials.from_json(flask.session['credentials'])
  if credentials.access_token_expired:
    return flask.redirect(flask.url_for('oauth2callback'))
  else:
    print 'Access_token: %s'  %credentials.access_token
    print 'Refresh_token: %s'  %credentials.refresh_token
    getActivities(credentials, 'me')

    return flask.redirect("http://www.google.com", code=302) #json.dumps( None )

@app.route('/oauth2callback')
def oauth2callback():
  flow = OAuth2WebServerFlow(client_id=client_id,
                           client_secret=client_secret,
                           scope=scope,
                           redirect_uri= redirect_uri,
                           approval_prompt='force',
                           response_type='code') 

  if 'code' not in flask.request.args:
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')
    credentials = flow.step2_exchange(auth_code)
    flask.session['credentials'] = credentials.to_json()
    return flask.redirect(flask.url_for('index'))

def getActivities(credentials, userId, query = ''):
    try:
        httpAuth = credentials.authorize( httplib2.Http() )
        service = discovery.build('plus', 'v1', http=httpAuth)
        person = service.people().get(userId=userId).execute()

        print('Got your ID: %s' % person['displayName'])
        print()
        print('%-040s -> %s' % ('[Activitity ID]', '[Content]'))

        # Don't execute the request until we reach the paging loop below.
        request = service.activities().list(userId=person['id'], collection='public')
        # Loop over every activity and print the ID and a short snippet of content.
        while request is not None:
          activities_doc = request.execute()
          for item in activities_doc.get('items', []):
            print('%-040s -> %s' % (item['id'], item['object']['content'][:40]))

          request = service.activities().list_next(request, activities_doc)

    except errors.HttpError, error:
        print "An error occurred: %s" %error
    return None

if __name__ == '__main__':
  import uuid
  app.secret_key = str(uuid.uuid4())
  app.debug = True
  app.run( port = 8000)
