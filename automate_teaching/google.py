import os 
import markdown
import datetime
import base64

from icalendar import Calendar, Event
import re
from bs4 import BeautifulSoup
import pytz
import pandas as pd
import numpy as np
from dateutil import parser
from tzlocal import get_localzone


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import mimetypes

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

def authenticate_google_app(credentials_path='gmail_credentials.json',token_path='gmail_token.json',SCOPES=None,service_name=None,service_version=None):
    
    """Authenticates and initializes a Google API service.

    Args:
        credentials_path (str): Path to the credentials file for the Google API.
        token_path (str): Path to the token file for storing user authentication.
        SCOPES (list): List of scopes for the Google API service.
        service_name (str): Name of the Google API service (e.g., 'gmail', 'calendar').
        service_version (str): Version of the Google API service (e.g., 'v1', 'v3').

    Returns:
        googleapiclient.discovery.Resource: Authenticated Google API service object.
    """

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # if creds and creds.expired and creds.refresh_token:
        #   creds.refresh(Request())
        # else:
        #   flow = InstalledAppFlow.from_client_secrets_file(
        #       credentials_path, SCOPES)
        #   creds = flow.run_local_server(port=0)
        #   # Save the credentials for the next run
        # with open(token_path, 'w') as token:
        #   token.write(creds.to_json())

        # Delete token if it exists because it isn't valid
        # if os.path.isfile(token_path):
        #   os.remove(token_path)

        # Obtain new token
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service = build(service_name, service_version, credentials=creds)

    return service

##################################################################################################
# Gmail class

class gmail:

    """Class for managing and sending Gmail messages. This class provides methods to send emails, manage labels, retrieve messages, and interact with Gmail via the Google API."""

    def __init__(self,credentials_path='credentials.json',token_path='token.json',sender=None):

        """Initializes an instance of the Gmail class.

        Args:
            credentials_path (str): Path to the Google API credentials file. Default is 'credentials.json'.
            token_path (str): Path to the token file for authentication. Default is 'token.json'.
            sender (str, optional): Default sender email address. Default is None.

        Attributes:
            service (googleapiclient.discovery.Resource): Authenticated Gmail API service object.
            sender (str): Email address used as the default sender.
        """

        self.service = authenticate_google_app(credentials_path,token_path,SCOPES=['https://mail.google.com/'],service_name='gmail',service_version='v1')

        self.sender = sender

    
    def add_message_label(self,message=None,message_id=None,label_names=None,label_ids=None):
        
        """Adds one of more labels to a Gmail message.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str): ID of the message to label.
            label_names (str or list): Name(s) of the label(s) to add.
            label_ids (str or list): ID(s) of the label(s) to add.

        Returns:
            None
            """
        if message_id is None:
            message_id = message['id']

        if label_ids is None:
            if type(label_names) is str:
                label_names = [label_names]
                label_ids = [self.get_label_id(x) for x in label_names]
        
        elif type(label_ids) is str:
            label_ids = [label_ids]
                
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'addLabelIds':label_ids}
        ).execute()

    def delete_message(self,message=None,message_id=None):

        """Permanently deletes a Gmail message.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str): ID of the message to delete.

        Returns:
            None
        """

        if message is not None:
            message_id = message['id']

        self.service.users().messages().delete(userId='me',id=message_id).execute()

    def get_all_labels(self):

        """Retrieves all Gmail labels for the user.

        Returns:
            pandas.DataFrame: DataFrame containing label names and metadata.
        """
        
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        df = pd.DataFrame(labels)

        return df


    def get_from_sender(self,sender,label_name=None,label_id=None):
        
        """Finds all messages from a specific sender.

        Args:
            sender (str): Email address of the sender to search for.
            label_name (str, optional): Name of the Gmail label to filter messages by. Default is None.
            label_id (str, optional): ID of the Gmail label to filter messages by. Default is None.

        Returns:
            list: List of message metadata dictionaries. Returns None if no messages are found.
        """
        
        if label_name is not None:
            
            label_id = self.get_label_id(label_name)

        results  = self.service.users().messages().list(userId='me',q='from:'+sender,labelIds=label_id).execute()
        messages = results.get('messages')
        
        return messages


    def get_label_id(self,label_name):
        
        """Retrieves the ID of a Gmail label by its name.

        Args:
            label_name (str): Name of the label.

        Returns:
            str: Label ID.
        """
        
        # Find all labels and label ids
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        # Search for desired label
        for n,label in enumerate(labels):
            if label['name'].lower() == label_name.lower():
                return label['id']


    def get_labeled_messages(self,label_name=None,label_id=None):
        
        """Retrieves messages with a specific Gmail label.

        Args:
            label_name (str, optional): Name of the label. Default is None.
            label_id (str, optional): ID of the label. Default is None.

        Returns:
            list: List of message metadata dictionaries. Returns None if no messages are found.
        """


        if label_name is not None:
            label_id = self.get_label_id(label_name)

        results  = self.service.users().messages().list(userId='me',labelIds=label_id).execute()
        messages = results.get('messages')
        return messages


    def get_message(self,message=None,message_id=None):

        """Retrieves a Gmail message by its ID.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str, optional): ID of the message to retrieve. Default is None.

        Returns:
            dict: Full Gmail message data.
        """

        if message is not None:
            message_id = message['id']

        message = self.service.users().messages().get(userId='me',id=message_id).execute()
        
        return message


    def get_message_return_path(self,message=None,message_id=None):

        """Retrieves the 'Return-Path' header of a Gmail message.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str, optional): ID of the message. Default is None.

        Returns:
            str: Email address from the 'Return-Path' header.
        """

        if message is not None:
            message_id = message['id']

        try:
            results  = self.service.users().messages().get(userId='me',id=message_id,format='metadata',metadataHeaders='Return-Path').execute()
            return_path = results['payload']['headers'][0]['value'][1:-1]
            
        except:
            results  = self.service.users().messages().get(userId='me',id=message_id,format='metadata',metadataHeaders='From').execute()
            return_path = results['payload']['headers'][0]['value'].split('<')[-1][:-1]

        return return_path

    def get_return_paths(self,messages=None):

        return_paths = []

        for m in messages:
            path = self.get_message_return_path(message=m)
            return_paths.append(path)

        return return_paths


    def make_message(self,sender=None,to=None,cc=None,bcc=None,subject = 'No subject',plain_text=None,html_text=None,markdown_text=None,send=True,attachments=None):

        """Creates and optionally sends a Gmail message.

        Args:
            sender (str, optional): Email address of the sender. Default is None.
            to (str or list, optional): Recipient email address(es). Default is None.
            cc (str or list, optional): CC email address(es). Default is None.
            bcc (str or list, optional): BCC email address(es). Default is None.
            subject (str): Email subject. Default is 'No subject'.
            plain_text (str, optional): Plain text content of the email. Default is None.
            html_text (str, optional): HTML content of the email. Default is None.
            markdown_text (str, optional): Markdown content for the email. Default is None.
            send (bool): Whether to send the email immediately. Default is True.
            attachments (str or list, optional): Path(s) to attachment files. Default is None.

        Returns:
            dict: Sent message metadata if `send=True`, else draft metadata.
        """

        try:

            # Initialize message
            mime_message=MIMEMultipart()

            # Headers
            if sender is not None:
                mime_message['From'] = sender
            else:
                mime_message['From'] = self.sender

            if to is not None:

                if type(to) is str:
                    to = [to]
                mime_message['To'] = ','.join(to)

            if cc is not None:

                if type(cc) is str:
                    cc = [cc]
                mime_message['Cc'] = ','.join(cc)

            if bcc is not None:

                if type(bcc) is str:
                    bcc = [bcc]
                mime_message['Bcc'] = ','.join(bcc)

            # Message text
            if plain_text is not None:

                plain=MIMEText(plain_text,'plain')
                mime_message.attach(plain)

            if html_text is not None:

                html=MIMEText(html_text,'html')
                mime_message.attach(html)

            if markdown_text is not None:
                html_text = markdown.markdown(markdown_text)
                html=MIMEText(html_text,'html')
                mime_message.attach(html)

            if plain_text is None and html_text is None:
                plain=MIMEText('No message','plain')
                mime_message.attach(plain)

            mime_message['Subject'] = subject

            # Attachments
            if attachments is not None:
                
                if type(attachments) is str:
                    attachments = [attachments]
                
                for attachment_path in attachments:
                    type_subtype, _ = mimetypes.guess_type(attachment_path)
                    maintype, subtype = type_subtype.split("/")



                    attach_file=MIMEApplication(open(attachment_path,"rb").read())
                    attach_file.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                    # Then attach to message attachment file    
                    mime_message.attach(attach_file)

            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()



            if send:

                create_message = {"raw": encoded_message}
                
                send_message = self.service.users().messages().send(userId="me", body=create_message).execute()
                print(F'Message Id: {send_message["id"]}')
                return send_message
            
            else:
                
                create_message = {"message": {"raw": encoded_message}}

                # pylint: disable=E1101
                draft = self.service.users().drafts().create(userId="me",body=create_message).execute()

                print(F'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')
                return draft

        except HttpError as error:
            print(F'An error occurred: {error}')
            send_message = None


    def move_message(self,message=None,message_id=None,old_label_name=None,new_label_name=None):
        
        """Moves a Gmail message from one label to another. To only delete a label, leave new_label_name=None. To only add a label, leave old_label_name=None.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str, optional): ID of the message to move. Default is None.
            old_label_name (str): Name of the current label.
            new_label_name (str): Name of the target label.

        Returns:
            None
        """

        if message is not None:
            message_id = message['id']
        
        old_label_id = self.get_label_id(old_label_name)
        new_label_id = self.get_label_id(new_label_name)
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'addLabelIds':[new_label_id],
                'removeLabelIds':[old_label_id]}
        ).execute()

    def move_messages(self,messages=None,old_label_name=None,new_label_name=None):

        """Moves a list of Gmail messages from one label to another. To only delete a label, leave new_label_name=None. To only add a label, leave old_label_name=None.

        Args:
            messages (list, optional): List of Gmail messages. Each element is a dictionary with keys 'id' and 'threadID'. Default is None.
            old_label_name (str): Name of the current label to be removed.
            new_label_name (str): Name of the target label to be added.

        Returns:
            None
        """

        for m in messages:

            self.move_message(message_id=m['id'],old_label_name=old_label_name,new_label_name=new_label_name)

    def remove_message_label(self,message=None,message_id=None,label_names=None,label_ids=None):
        
        """Removes one or more labels from a Gmail message.

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str): ID of the message to label.
            label_names (str or list): Name(s) of the label(s) to remove.
            label_ids (str or list): ID(s) of the label(s) to remove.

        Returns:
            None
        """
        
        if message_id is None:
            message_id = message['id']
        
        if label_ids is None:
            if type(label_names) is str:
                label_names = [label_names]
                label_ids = [self.get_label_id(x) for x in label_names]
        
        elif type(label_ids) is str:
            label_ids = [label_ids]
                
        
        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={
                'removeLabelIds':label_ids}
        ).execute()
        
        
    def trash_message(self,message=None,message_id=None):

        """Moves a Gmail message to 

        Args:
            message (dict, optional): Message metadata dictionary. Default is None.
            message_id (str): ID of the message to delete. Default is None.

        Returns:
            None
        """

        if message is not None:
            message_id = message['id']

        self.service.users().messages().trash(userId='me',id=message_id).execute()


##################################################################################################
# Google Calendar class

class calendar:

    """Class for interacting with Google Calendar. This class provides methods to add, find, delete, and import events
    from Google Calendar, as well as parse `.ics` files for event details."""

    def __init__(self,credentials_path='credentials.json',token_path='token.json'):

        """Initializes a calendar instance.

        Args:
            credentials_path (str): Path to the Google Calendar credentials file. Default is 'credentials.json'.
            token_path (str): Path to the token file for authentication. Default is 'token.json'.

        Attributes:
            service (googleapiclient.discovery.Resource): Google API service object for calendar interactions.
            calendar_ids (pandas.Series): Calendar IDs, with calendar names as indices.
            primary_calendar (str): Name of the primary calendar for the account.
            primary_calendar_id (str): ID of the primary calendar for the account.
        """

        # self.service = build('calendar', 'v3', credentials=creds)
        self.service = authenticate_google_app(credentials_path,token_path,SCOPES=['https://www.googleapis.com/auth/calendar'],service_name='calendar',service_version='v3')

        # Get calendars and IDs
        calendar_ids = pd.Series(name='ids',dtype=str)

        # Following code taken from API docs: https://developers.google.com/calendar/api/v3/reference/calendarList/list#python
        page_token = None
        while True:

            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendar_ids.loc[calendar_list_entry['summary']] = calendar_list_entry['id']
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break


        self.calendar_ids = calendar_ids

        # Identify the primary calendar. Adapted from https://developers.google.com/calendar/api/v3/reference/calendars/get#python
        self.primary_calendar = self.service.calendars().get(calendarId='primary').execute()['summary']
        self.primary_calendar_id = self.calendar_ids[self.primary_calendar]


    def add_event(self,start,end=None,duration=0,duration_units='H',title='Event',description=None,calendar_name=None,calendar_id=None,time_zone=None,all_day=False):

        """Adds a single event to a Google Calendar.

        Args:
            start (str): Start time of the event. Format: "[month name] dd" or "yyyy hh:mm:ss[am/pm]". E.g. "January 4, 2022 4pm"
            end (str, optional): End date and time of the event. Default is None.
            duration (float, optional): Duration of the event. Units to be specified with 'duration_units'. Default is 0.
            duration_units (str, optional): Time units for duration. Default is 'H' (hourly). See: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
            title (str): Title of the event. Default is 'Event'.
            description (str, optional): Description of the event. Default is None.
            calendar_name (str, optional): Name of the calendar to add the event to. Default is None.
            calendar_id (str, optional): ID of the calendar to add the event to. Default is None.
            time_zone (str, optional): Time zone for the event in TZ identifier format (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) Default is None.
            all_day (bool, optional): If True, creates an all-day event. Default is False.

        Raises:
            ValueError: If `calendar_name` and `calendar_id` do not reference the same calendar.

        Returns:
                None
        """

        if description is None:
            description = 'Added by automate_teaching.'
        else:
            description += '\n\nAdded by automate_teaching.'

        start = pd.to_datetime(start).date() if all_day else pd.to_datetime(start)

        if end is not None:
            end = pd.to_datetime(end).date() if all_day else pd.to_datetime(end)
        else:
            if duration_units is None:
                duration_units = 'H'
            if all_day:
                end = start + pd.Timedelta(days=1)
            else:
                end = start + pd.Timedelta(duration, duration_units)

        if calendar_id is not None and calendar_name is not None:
            if calendar_id != self.calendar_ids[calendar_name]:
                raise ValueError('calendar_id and calendar_name do not reference the same calendar.')
        elif calendar_name is not None:
            calendar_id = self.calendar_ids[calendar_name]

        if calendar_id is None:
            calendar_id = self.primary_calendar_id

        if all_day:
            event = {
                'summary': title,
                'description': description,
                'start': {'date': start.isoformat()},
                'end': {'date': end.isoformat()}
            }
        else:
            if time_zone is None:
                time_zone = self.service.calendars().get(calendarId=calendar_id).execute()['timeZone']

            tz = pytz.timezone(time_zone)
            utc_offset = tz.utcoffset(start)
            seconds = utc_offset.seconds + utc_offset.days * 86400
            utc_sign = '-' if seconds < 0 else '+'
            seconds = abs(seconds)
            hours = int(seconds / 3600)
            minutes = round((seconds % 3600) / 60)
            UTC_HH = utc_sign + f'{abs(hours):02d}'
            UTC_MM = f'{seconds % 3600 // 60:02d}'

            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start.strftime('%Y-%m-%dT%H:%M:%S' + UTC_HH + ':' + UTC_MM),
                    'timeZone': time_zone,
                },
                'end': {
                    'dateTime': end.strftime('%Y-%m-%dT%H:%M:%S' + UTC_HH + ':' + UTC_MM),
                    'timeZone': time_zone,
                },
            }

        self.service.events().insert(calendarId=calendar_id, body=event).execute()

    def delete_events(self,events=None,calendar_name=None,calendar_id=None):

        """Deletes events from a Google Calendar.

        Args:
            events (list): List of event dictionaries to delete.
            calendar_name (str, optional): Name of the calendar containing the events. Default is None.
            calendar_id (str, optional): ID of the calendar containing the events. Default is None.

        Raises:
            ValueError: If `calendar_name` and `calendar_id` do not reference the same calendar.
        """

        if calendar_id is not None and calendar_name is not None:
            if calendar_id != self.calendar_ids[calendar_name]:
                raise ValueError('calendar_id and calendar_name do not reference the same calendar.')
        elif calendar_name is not None:
            calendar_id = self.calendar_ids[calendar_name]

        # Set calendar_id to primary if calendar_id or calendar_name are supplied
        if calendar_id == None:
            calendar_id = self.primary_calendar_id
    
        # Iterate and delete
        for event in events:
            self.service.events().delete(calendarId=calendar_id, eventId=event.get('id')).execute()

    def export_to_ics(self, event, ics_path='event.ics'):
        
        """
        Converts a Google Calendar event to an ICS file format.

        Args:
            event (dict): A dictionary representing a Google Calendar event. 
                Must contain the following keys:
                    - 'summary' (str): The title of the event.
                    - 'description' (str, optional): The description of the event.
                    - 'location' (str, optional): The location of the event.
                    - 'start' (dict): The event start time, with keys:
                        - 'dateTime' (str, optional): Start datetime in ISO 8601 format.
                        - 'date' (str, optional): Start date if no specific time is provided.
                        - 'timeZone' (str, optional): Timezone for the event start (default is 'UTC').
                    - 'end' (dict): The event end time, with keys:
                        - 'dateTime' (str, optional): End datetime in ISO 8601 format.
                        - 'date' (str, optional): End date if no specific time is provided.
            ics_path (str, optional): The file path to save the generated ICS file. 
                Default is 'event.ics'.

        Returns:
            None

        Raises:
            KeyError: If required keys ('summary', 'start', 'end') are missing from the event.
            ValueError: If datetime parsing fails or invalid timezone is specified.
        """

        cal = Calendar()
        cal_event = Event()

        cal_event.add('summary', event['summary'])
        cal_event.add('description', event.get('description', ''))
        cal_event.add('location', event.get('location', ''))

        # Extract start and end times
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))

        # Parse datetime and ensure proper timezone handling
        def parse_datetime_with_tz(dt, timezone_str):
            """Parse a datetime string and ensure timezone is applied."""
            dt_obj = parser.parse(dt)  # Parse the datetime string
            timezone = pytz.timezone(timezone_str)  # Get the timezone
            if dt_obj.tzinfo is None:  # If naive, localize to the specified timezone
                return timezone.localize(dt_obj)
            return dt_obj  # Return as-is if already timezone-aware

        # Get the time zone for the event, or default to UTC
        timezone_str = event['start'].get('timeZone', 'UTC')
        
        # Convert start and end times to timezone-aware datetime
        dtstart = parse_datetime_with_tz(start, timezone_str)
        dtend = parse_datetime_with_tz(end, timezone_str)

        # Add the event's start and end times with TZID
        cal_event.add('dtstart', dtstart, parameters={'TZID': timezone_str})
        cal_event.add('dtend', dtend, parameters={'TZID': timezone_str})

        # Add the current timestamp
        cal_event.add('dtstamp', datetime.datetime.now().astimezone(get_localzone()))

        # Add the event to the calendar
        cal.add_component(cal_event)

        # Generate ICS content
        ics_content = cal.to_ical()

        # Save to ICS file
        with open(ics_path, 'wb') as ics_file:
            ics_file.write(ics_content)

        print(f"Event exported to {ics_path} successfully.")

        
    def find_future_events(self,title_contains=None,description_contains=None,calendar_name=None,calendar_id=None,maxResults=1000):

        """Finds future events matching specified criteria.

        Args:
            title_contains (str, optional): Search keyword for the event title. Default is None.
            description_contains (str, optional): Search keyword for the event description. Default is None.
            calendar_name (str, optional): Name of the calendar to search. Default is None.
            calendar_id (str, optional): ID of the calendar to search. Default is None.
            maxResults (int): Maximum number of results to return. Default is 1000.

        Returns:
            list: List of matching event dictionaries.
        """

        if calendar_id is not None and calendar_name is not None:
            if calendar_id != self.calendar_ids[calendar_name]:
                raise ValueError('calendar_id and calendar_name do not reference the same calendar.')
        elif calendar_name is not None:
            calendar_id = self.calendar_ids[calendar_name]

        # Set calendar_id to primary if calendar_id or calendar_name are supplied
        if calendar_id == None:
            calendar_id = self.primary_calendar_id
        
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = (
            self.service
                .events()
                .list(calendarId=calendar_id,
                      timeMin=now,
                      maxResults=maxResults,
                      singleEvents=True,
                      orderBy='startTime')
                .execute()
        )
        all_events = events_result.get('items', [])

        # if no filters specified, return everything
        if title_contains is None and description_contains is None:
            return all_events

        events = []
        for event in all_events:
            summary = event.get('summary', '')
            description = event.get('description', '')

            if title_contains and description_contains:
                if title_contains in summary and description_contains in description:
                    events.append(event)

            elif title_contains:
                if title_contains in summary:
                    events.append(event)

            elif description_contains:
                if description_contains in description:
                    events.append(event)

        return events

    
    def import_from_ics(self, ics_path=None, calendar_name=None, calendar_id=None, delete_ics=False):
        
        """Imports events from an `.ics` file into a Google Calendar.

        Args:
            ics_path (str, optional): Path to the `.ics` file. Default is None.
            calendar_name (str, optional): Name of the calendar to import events into. Default is None.
            calendar_id (str, optional): ID of the calendar to import events into. Default is None.
            delete_ics (bool): Whether to delete the `.ics` file after import. Default is False.

        Raises:
            FileNotFoundError: If the `.ics` file does not exist.
            ValueError: If `calendar_name` and `calendar_id` do not reference the same calendar.
            ValueError: If the `.ics` file cannot be parsed or contains invalid data.

        Returns:
            None
        """
        
        # Validate input arguments
        if not ics_path or not os.path.exists(ics_path):
            raise FileNotFoundError(f"ICS file not found: {ics_path}")

        if calendar_name and calendar_id:
            if calendar_id != self.calendar_ids.get(calendar_name):
                raise ValueError("calendar_id and calendar_name do not reference the same calendar.")
        elif calendar_name:
            calendar_id = self.calendar_ids.get(calendar_name)

        if not calendar_id:
            calendar_id = self.primary_calendar_id

        # Parse events from the ICS file
        try:
            events = self.parse_ics(ics_path)
        except Exception as e:
            raise ValueError(f"Failed to parse ICS file: {e}")

        for event in events:
            print(f"Importing event: {event.get('summary', 'Unnamed Event')}")
            print(f"Start: {event.get('start')}")
            print(f"End: {event.get('end')}")

            try:
                self.service.events().insert(calendarId=calendar_id, body=event).execute()
            except Exception as e:
                print(f"Failed to import event: {event.get('summary', 'Unnamed Event')} - {e}")


        # Optionally delete the ICS file
        if delete_ics:
            try:
                os.remove(ics_path)
            except Exception as e:
                print(f"Failed to delete ICS file: {ics_path} - {e}")

    def make_multiple_events(self,title='Event',description=None,start_date=None,end_date=None,event_time=None,duration=None,duration_units='H',freq='B',periods=None,calendar_name=None,calendar_id=None,time_zone=None):
    
        """Creates multiple recurring events in a Google Calendar.
        
        Args:
            title (str): Title of the events. Default is 'Event'.
            description (str, optional): Description of the events. Default is None.
            start_date (str): Start time of the recurring event. Format: "[month name] dd" or "yyyy hh:mm:ss[am/pm]". E.g. "January 4, 2022 4pm"
            end_date (str, optional): End date and time of the recurring event. Default is None.
            event_time (str, optional): Start time of the events. Default is None.
            duration (float, optional): Duration of each event. Default is None.
            duration_units (str): Units for the event duration. Default is 'H' (hourly). See: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
            freq (str): Frequency of recurrence. Default is 'B' (business day). See: https://pandas.pydata.org/pandas-docs/stable/user_guide/timeseries.html#offset-aliases
            periods (int, optional): Number of occurrences at specified frequency. Default is None.
            calendar_name (str, optional): Name of the calendar to add the events to. Default is None.
            calendar_id (str, optional): ID of the calendar to add the events to. Default is None.
            time_zone (str, optional): Time zone for the events in TZ identifier format (https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) Default is None.. Default is None.
        """

        # Concatenate beginning of recurring date and event time if necessary
        if event_time is not None:
            start_date = start_date+' '+event_time

        # Generate range of starting dates and times
        dates = pd.date_range(start=start_date,end=end_date,periods=periods,freq=freq,tz=time_zone)

        # Generate range of ending dates and times
        ending_dates = dates + pd.Timedelta(duration, unit=duration_units)

        # Add events to calendar
        for n,time in enumerate(dates):

            self.add_event(start = time,end=ending_dates[n],duration=duration,title=title,description=description,calendar_name=calendar_name,calendar_id=calendar_id,time_zone=time_zone)


    def parse_ics(self,ics_path):
        
        """Parses an `.ics` file into a list of event dictionaries.

        Args:
            ics_path (str): The file path to the `.ics` file to be parsed.

        Returns:
            list: A list of dictionaries, each representing an event. 
            Each dictionary contains the following keys:
                - 'summary' (str, optional): The title of the event.
                - 'location' (str, optional): The location of the event.
                - 'start' (dict): The start time of the event with the structure:
                    - 'dateTime' (str): ISO 8601 formatted datetime string.
                    - 'timeZone' (str): The timezone of the event start.
                - 'end' (dict): The end time of the event with the structure:
                    - 'dateTime' (str): ISO 8601 formatted datetime string.
                    - 'timeZone' (str): The timezone of the event end.
                - 'description' (str, optional): A description of the event.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the `.ics` file contains invalid or malformed data.
        """

        def parse_datetime(prop):
            """Parse a datetime property and ensure time zone is valid."""
            dt = prop.dt
            if not isinstance(dt, datetime.datetime):
                dt = parser.parse(str(dt))  # Use dateutil to parse ISO format
            tzinfo = dt.tzinfo or pytz.UTC  # Default to UTC if no time zone is set
            return {
                'dateTime': dt.isoformat(),
                'timeZone': str(tzinfo.zone) if hasattr(tzinfo, 'zone') else 'UTC'
            }

        events = []
        with open(ics_path, 'r') as rf:
            ical = Calendar.from_ical(rf.read())

            for comp in ical.walk():
                if comp.name == 'VEVENT':
                    event = {}

                    for name, prop in comp.property_items():
                        if name == 'SUMMARY':
                            event['summary'] = prop
                        elif name == 'LOCATION':
                            event['location'] = prop
                        elif name == 'DTSTART':
                            event['start'] = parse_datetime(prop)
                        elif name == 'DTEND':
                            event['end'] = parse_datetime(prop)
                        elif name == 'DESCRIPTION':
                            event['description'] = prop

                    # Ensure required fields are present
                    if 'start' in event and 'end' in event:
                        events.append(event)

        return events