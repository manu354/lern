from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools

import gkeepapi
from twisted.internet import task
from twisted.internet import reactor
import gKeep

from config import config

SCOPES = 'https://www.googleapis.com/auth/calendar'
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)
service = build('calendar', 'v3', http=creds.authorize(Http()))

# Call the Calendar API
now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

TIMEZONE = service.settings().get(setting='timezone').execute()['value']


def eventSchema(title, desc, dateCreated):
    event = {
        'summary': title + ": " + desc,
        'description': desc,
        'start': {
            'dateTime': dateCreated,
            'timeZone': TIMEZONE
        },
        'end': {
            'dateTime': dateCreated,
            'timeZone': TIMEZONE
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    return event


def createEvent(title, desc, ID, dateCreated):
    event = eventSchema(title, desc, dateCreated)
    event = service.events().insert(calendarId=ID, body=event).execute()
    print(event.get('htmlLink'))


calendar = {
    'summary': "Spaced Repetition",
}
calID = None
# Loop through calendars to see if one is already called "Spaced"
page_token = None
while True:
    calendar_list = service.calendarList().list(pageToken=page_token).execute()
    for calendar_list_entry in calendar_list['items']:
        print(calendar_list_entry['summary'])
        if calendar_list_entry['summary'] == calendar['summary']:
            calID = calendar_list_entry['id']
            break
    page_token = calendar_list.get('nextPageToken')
    if not page_token:
        break

# If there is no calendar, create it
if not calID:
    created_calendar = service.calendars().insert(body=calendar).execute()
    calID = created_calendar['id']


timeout = 10.0  # seconds

keep = gkeepapi.Keep()
success = keep.login(config.USERNAME, config.PASSWORD)


def doWork():
    # do work here
    print("running")
    keep.sync()
    gnote = keep.find(labels=[keep.findLabel('spaced')], archived=False, trashed=False)
    for item in gnote:
        time = item.timestamps.created.strftime('%Y-%m-%d')
        time += "T00:00:00-00:00"
        gKeep.addToList(keep, item) # move this later to after item.del
        createEvent(item.title, item.text, calID, time)
        item.delete()
    print("done")

l = task.LoopingCall(doWork)
l.start(timeout)  # call every sixty seconds

reactor.run()
