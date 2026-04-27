"""Google API integrations for Gmail and Google Calendar."""

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


def authenticate_google_app(
    credentials_path='gmail_credentials.json',
    token_path='gmail_token.json',
    SCOPES=None,
    service_name=None,
    service_version=None,
):
    """Authenticate and return a Google API service object.

    Reads cached credentials from token_path if available. When a cached
    token exists but has expired, it is refreshed silently using the stored
    refresh token. Only when no valid token exists at all is the full OAuth
    browser flow triggered. The (potentially refreshed) token is always
    written back to token_path so subsequent calls can reuse it.

    Args:
        credentials_path (str, optional): Path to the OAuth client secrets
            file downloaded from the Google Cloud console. Defaults to
            'gmail_credentials.json'.
        token_path (str, optional): Path where the user token is cached.
            Defaults to 'gmail_token.json'.
        SCOPES (list of str, optional): OAuth scopes to request.
            Defaults to None.
        service_name (str, optional): Google API service identifier
            (e.g., 'gmail', 'calendar'). Defaults to None.
        service_version (str, optional): API version string (e.g., 'v1',
            'v3'). Defaults to None.

    Returns:
        googleapiclient.discovery.Resource: Authenticated API service
            object.
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        # Refresh silently when a refresh token is available; only fall back
        # to the full browser OAuth flow when the token cannot be refreshed.
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return build(service_name, service_version, credentials=creds)


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

class Gmail:
    """Manage and send Gmail messages via the Gmail API.

    Provides methods to send emails, manage labels, retrieve messages,
    and interact with Gmail programmatically.
    """

    def __init__(self, credentials_path='credentials.json', token_path='token.json', sender=None):
        """Initialize a Gmail instance.

        Args:
            credentials_path (str, optional): Path to the Google API OAuth
                credentials file. Defaults to 'credentials.json'.
            token_path (str, optional): Path to the cached token file.
                Defaults to 'token.json'.
            sender (str, optional): Default sender email address used when
                no sender is specified in make_message. Defaults to None.
        """
        self.service = authenticate_google_app(
            credentials_path,
            token_path,
            SCOPES=['https://mail.google.com/'],
            service_name='gmail',
            service_version='v1',
        )
        self.sender = sender

    def add_message_label(self, message=None, message_id=None, label_names=None, label_ids=None):
        """Add one or more labels to a Gmail message.

        Args:
            message (dict, optional): Message metadata dict containing an
                'id' key. Used when message_id is not provided. Defaults
                to None.
            message_id (str, optional): Gmail message ID. Defaults to None.
            label_names (str or list of str, optional): Label name(s) to
                add. Defaults to None.
            label_ids (str or list of str, optional): Label ID(s) to add.
                Takes precedence over label_names if both are provided.
                Defaults to None.
        """
        if message_id is None:
            message_id = message['id']

        if label_ids is None:
            if isinstance(label_names, str):
                label_names = [label_names]
            label_ids = [self.get_label_id(x) for x in label_names]
        elif isinstance(label_ids, str):
            label_ids = [label_ids]

        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': label_ids},
        ).execute()

    def delete_message(self, message=None, message_id=None):
        """Permanently delete a Gmail message.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.
        """
        if message is not None:
            message_id = message['id']
        self.service.users().messages().delete(userId='me', id=message_id).execute()

    def get_all_labels(self):
        """Retrieve all Gmail labels for the authenticated account.

        Returns:
            pandas.DataFrame: DataFrame with one row per label, containing
                label names and metadata returned by the API.
        """
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        return pd.DataFrame(labels)

    def get_from_sender(self, sender, label_name=None, label_id=None):
        """Find all messages from a specific sender.

        Args:
            sender (str): Email address of the sender to search for.
            label_name (str, optional): Filter by this label name. Resolves
                to a label ID via get_label_id. Defaults to None.
            label_id (str, optional): Filter by this label ID directly.
                Takes precedence over label_name if both are provided.
                Defaults to None.

        Returns:
            list of dict or None: List of message metadata dicts, or None
                if no messages are found.
        """
        if label_name is not None:
            label_id = self.get_label_id(label_name)

        # The Gmail API expects labelIds as a list; wrap the single ID.
        label_ids = [label_id] if label_id is not None else None
        results = self.service.users().messages().list(
            userId='me', q='from:' + sender, labelIds=label_ids
        ).execute()
        return results.get('messages')

    def get_label_id(self, label_name):
        """Return the ID of a Gmail label by its display name.

        Args:
            label_name (str): The exact label name (case-insensitive).

        Returns:
            str or None: The label ID, or None if no matching label is
                found.
        """
        results = self.service.users().labels().list(userId='me').execute()
        for label in results.get('labels', []):
            if label['name'].lower() == label_name.lower():
                return label['id']
        return None

    def get_labeled_messages(self, label_name=None, label_id=None):
        """Retrieve all messages with a specific label.

        Args:
            label_name (str, optional): Label name to filter by. Resolves
                to a label ID via get_label_id. Defaults to None.
            label_id (str, optional): Label ID to filter by directly.
                Takes precedence over label_name if both are provided.
                Defaults to None.

        Returns:
            list of dict or None: List of message metadata dicts, or None
                if no messages are found.
        """
        if label_name is not None:
            label_id = self.get_label_id(label_name)

        # The Gmail API expects labelIds as a list; wrap the single ID.
        label_ids = [label_id] if label_id is not None else None
        results = self.service.users().messages().list(
            userId='me', labelIds=label_ids
        ).execute()
        return results.get('messages')

    def get_message(self, message=None, message_id=None):
        """Retrieve a full Gmail message by its ID.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.

        Returns:
            dict: Full Gmail message payload returned by the API.
        """
        if message is not None:
            message_id = message['id']
        return self.service.users().messages().get(userId='me', id=message_id).execute()

    def get_message_return_path(self, message=None, message_id=None):
        """Return the 'Return-Path' (or 'From') address of a message.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.

        Returns:
            str: The sender email address extracted from the Return-Path or
                From header.
        """
        if message is not None:
            message_id = message['id']

        try:
            results = self.service.users().messages().get(
                userId='me', id=message_id, format='metadata', metadataHeaders='Return-Path'
            ).execute()
            return results['payload']['headers'][0]['value'][1:-1]
        except Exception:
            results = self.service.users().messages().get(
                userId='me', id=message_id, format='metadata', metadataHeaders='From'
            ).execute()
            return results['payload']['headers'][0]['value'].split('<')[-1][:-1]

    def get_return_paths(self, messages=None):
        """Return the sender address for each message in a list.

        Args:
            messages (list of dict): List of message metadata dicts, each
                containing an 'id' key.

        Returns:
            list of str: Return-Path or From addresses, one per message.
        """
        return [self.get_message_return_path(message=m) for m in messages]

    def make_message(
        self,
        sender=None,
        to=None,
        cc=None,
        bcc=None,
        subject='No subject',
        plain_text=None,
        html_text=None,
        markdown_text=None,
        send=True,
        attachments=None,
    ):
        """Create and optionally send a Gmail message.

        At least one of plain_text, html_text, or markdown_text should be
        provided. Markdown is converted to HTML before sending. If none is
        provided, the body defaults to 'No message'.

        Args:
            sender (str, optional): Sender email address. Falls back to
                self.sender if not provided. Defaults to None.
            to (str or list of str, optional): Recipient address(es).
                Defaults to None.
            cc (str or list of str, optional): CC address(es). Defaults to
                None.
            bcc (str or list of str, optional): BCC address(es). Defaults
                to None.
            subject (str, optional): Email subject line. Defaults to
                'No subject'.
            plain_text (str, optional): Plain-text email body. Defaults to
                None.
            html_text (str, optional): HTML email body. Defaults to None.
            markdown_text (str, optional): Markdown email body (converted to
                HTML). Defaults to None.
            send (bool, optional): If True, send immediately; if False,
                save as a draft. Defaults to True.
            attachments (str or list of str, optional): File path(s) to
                attach. Defaults to None.

        Returns:
            dict or None: Sent message metadata if send=True, draft metadata
                if send=False, or None if an HTTP error occurs.
        """
        try:
            mime_message = MIMEMultipart()

            mime_message['From'] = sender if sender is not None else self.sender

            if to is not None:
                if isinstance(to, str):
                    to = [to]
                mime_message['To'] = ','.join(to)

            if cc is not None:
                if isinstance(cc, str):
                    cc = [cc]
                mime_message['Cc'] = ','.join(cc)

            if bcc is not None:
                if isinstance(bcc, str):
                    bcc = [bcc]
                mime_message['Bcc'] = ','.join(bcc)

            if plain_text is not None:
                mime_message.attach(MIMEText(plain_text, 'plain'))

            if html_text is not None:
                mime_message.attach(MIMEText(html_text, 'html'))

            if markdown_text is not None:
                mime_message.attach(MIMEText(markdown.markdown(markdown_text), 'html'))

            if plain_text is None and html_text is None and markdown_text is None:
                mime_message.attach(MIMEText('No message', 'plain'))

            mime_message['Subject'] = subject

            if attachments is not None:
                if isinstance(attachments, str):
                    attachments = [attachments]
                for attachment_path in attachments:
                    # Use a context manager so the file handle is always closed,
                    # even if an exception is raised mid-loop.
                    with open(attachment_path, 'rb') as af:
                        attach_file = MIMEApplication(af.read())
                    attach_file.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=os.path.basename(attachment_path),
                    )
                    mime_message.attach(attach_file)

            encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

            if send:
                create_message = {'raw': encoded_message}
                sent = self.service.users().messages().send(
                    userId='me', body=create_message
                ).execute()
                print('Message Id: ' + sent['id'])
                return sent
            else:
                create_message = {'message': {'raw': encoded_message}}
                draft = self.service.users().drafts().create(
                    userId='me', body=create_message
                ).execute()
                print('Draft id: ' + draft['id'])
                return draft

        except HttpError as error:
            print('An error occurred: ' + str(error))
            return None

    def move_message(self, message=None, message_id=None, old_label_name=None, new_label_name=None):
        """Move a Gmail message from one label to another.

        Pass only new_label_name to add a label without removing one.
        Pass only old_label_name to remove a label without adding one.
        Only non-None label IDs are sent to the API, so omitting one of the
        name arguments simply skips that operation rather than sending a
        None value to the API.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.
            old_label_name (str, optional): Label to remove. Defaults to
                None.
            new_label_name (str, optional): Label to add. Defaults to None.
        """
        if message is not None:
            message_id = message['id']

        body = {}

        if new_label_name is not None:
            new_label_id = self.get_label_id(new_label_name)
            if new_label_id is not None:
                body['addLabelIds'] = [new_label_id]

        if old_label_name is not None:
            old_label_id = self.get_label_id(old_label_name)
            if old_label_id is not None:
                body['removeLabelIds'] = [old_label_id]

        if body:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body,
            ).execute()

    def move_messages(self, messages=None, old_label_name=None, new_label_name=None):
        """Move a list of Gmail messages from one label to another.

        Args:
            messages (list of dict): List of message metadata dicts, each
                with an 'id' key.
            old_label_name (str, optional): Label to remove from each
                message. Defaults to None.
            new_label_name (str, optional): Label to add to each message.
                Defaults to None.
        """
        for m in messages:
            self.move_message(
                message_id=m['id'],
                old_label_name=old_label_name,
                new_label_name=new_label_name,
            )

    def remove_message_label(self, message=None, message_id=None, label_names=None, label_ids=None):
        """Remove one or more labels from a Gmail message.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.
            label_names (str or list of str, optional): Label name(s) to
                remove. Defaults to None.
            label_ids (str or list of str, optional): Label ID(s) to remove.
                Defaults to None.
        """
        if message_id is None:
            message_id = message['id']

        if label_ids is None:
            if isinstance(label_names, str):
                label_names = [label_names]
            label_ids = [self.get_label_id(x) for x in label_names]
        elif isinstance(label_ids, str):
            label_ids = [label_ids]

        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': label_ids},
        ).execute()

    def trash_message(self, message=None, message_id=None):
        """Move a Gmail message to the trash.

        Args:
            message (dict, optional): Message metadata dict with an 'id'
                key. Defaults to None.
            message_id (str, optional): Gmail message ID. Defaults to None.
        """
        if message is not None:
            message_id = message['id']
        self.service.users().messages().trash(userId='me', id=message_id).execute()


# ---------------------------------------------------------------------------
# Google Calendar
# ---------------------------------------------------------------------------

class GoogleCalendar:
    """Interact with Google Calendar via the Calendar API.

    Provides methods to add, find, delete, and import events, and to
    parse .ics files for event data.
    """

    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        """Initialize a GoogleCalendar instance.

        Authenticates with the Google Calendar API and retrieves the list
        of available calendars.

        Args:
            credentials_path (str, optional): Path to the OAuth client
                secrets file. Defaults to 'credentials.json'.
            token_path (str, optional): Path to the cached token file.
                Defaults to 'token.json'.
        """
        self.service = authenticate_google_app(
            credentials_path,
            token_path,
            SCOPES=['https://www.googleapis.com/auth/calendar'],
            service_name='calendar',
            service_version='v3',
        )

        calendar_ids = pd.Series(name='ids', dtype=str)
        page_token = None
        while True:
            calendar_list = self.service.calendarList().list(pageToken=page_token).execute()
            for entry in calendar_list['items']:
                calendar_ids.loc[entry['summary']] = entry['id']
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        self.calendar_ids = calendar_ids
        self.primary_calendar = self.service.calendars().get(calendarId='primary').execute()['summary']
        self.primary_calendar_id = self.calendar_ids[self.primary_calendar]

    def _resolve_calendar_id(self, calendar_name=None, calendar_id=None):
        """Return a resolved calendar ID from a name or ID, with validation.

        Args:
            calendar_name (str, optional): Calendar display name. Defaults
                to None.
            calendar_id (str, optional): Calendar ID. Defaults to None.

        Returns:
            str: The resolved calendar ID, falling back to the primary
                calendar if neither argument is provided.

        Raises:
            ValueError: If both arguments are provided but refer to
                different calendars.
        """
        if calendar_id is not None and calendar_name is not None:
            if calendar_id != self.calendar_ids[calendar_name]:
                raise ValueError('calendar_id and calendar_name do not reference the same calendar.')
        elif calendar_name is not None:
            calendar_id = self.calendar_ids[calendar_name]

        return calendar_id if calendar_id is not None else self.primary_calendar_id

    def add_event(
        self,
        start,
        end=None,
        duration=0,
        duration_units='H',
        title='Event',
        description=None,
        calendar_name=None,
        calendar_id=None,
        time_zone=None,
        all_day=False,
    ):
        """Add a single event to a Google Calendar.

        Args:
            start (str): Event start time. Accepts natural-language strings
                parsed by pandas (e.g., 'January 4, 2022 4pm').
            end (str, optional): Event end time. Defaults to None, in which
                case ``duration`` is used.
            duration (float, optional): Duration of the event in
                ``duration_units``. Ignored when ``end`` is provided.
                Defaults to 0.
            duration_units (str, optional): Pandas offset alias for the
                duration unit (e.g., 'H' for hours). Defaults to 'H'.
            title (str, optional): Event title. Defaults to 'Event'.
            description (str, optional): Event description. Defaults to
                None.
            calendar_name (str, optional): Target calendar name. Defaults
                to None (uses primary calendar).
            calendar_id (str, optional): Target calendar ID. Defaults to
                None (uses primary calendar).
            time_zone (str, optional): IANA time zone identifier (e.g.,
                'America/Los_Angeles'). Defaults to None (uses the
                calendar's default time zone).
            all_day (bool, optional): If True, create an all-day event.
                Defaults to False.

        Raises:
            ValueError: If calendar_name and calendar_id refer to different
                calendars.
        """
        if description is None:
            description = 'Added by automate_teaching.'
        else:
            description += '\n\nAdded by automate_teaching.'

        calendar_id = self._resolve_calendar_id(calendar_name, calendar_id)

        start = pd.to_datetime(start).date() if all_day else pd.to_datetime(start)

        if end is not None:
            end = pd.to_datetime(end).date() if all_day else pd.to_datetime(end)
        else:
            if all_day:
                end = start + pd.Timedelta(days=1)
            else:
                end = start + pd.Timedelta(duration, duration_units)

        if all_day:
            event = {
                'summary': title,
                'description': description,
                'start': {'date': start.isoformat()},
                'end': {'date': end.isoformat()},
            }
        else:
            if time_zone is None:
                time_zone = self.service.calendars().get(calendarId=calendar_id).execute()['timeZone']

            tz = pytz.timezone(time_zone)

            # pd.to_datetime may return a timezone-aware Timestamp if the
            # input string contains timezone info. pytz.utcoffset requires a
            # naive datetime, so strip any tzinfo before the call.
            start_naive = start.replace(tzinfo=None) if hasattr(start, 'tzinfo') else start
            end_naive = end.replace(tzinfo=None) if hasattr(end, 'tzinfo') else end

            utc_offset = tz.utcoffset(start_naive)
            # timedelta.total_seconds() gives a signed float, which is the
            # correct value to use for negative offsets (e.g. UTC-08:00).
            total_seconds = int(utc_offset.total_seconds())
            utc_sign = '-' if total_seconds < 0 else '+'
            total_seconds = abs(total_seconds)
            UTC_HH = utc_sign + f'{total_seconds // 3600:02d}'
            UTC_MM = f'{total_seconds % 3600 // 60:02d}'

            # Localise the naive datetimes so strftime formats them correctly.
            start_local = tz.localize(start_naive)
            end_local = tz.localize(end_naive)

            event = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_local.strftime('%Y-%m-%dT%H:%M:%S' + UTC_HH + ':' + UTC_MM),
                    'timeZone': time_zone,
                },
                'end': {
                    'dateTime': end_local.strftime('%Y-%m-%dT%H:%M:%S' + UTC_HH + ':' + UTC_MM),
                    'timeZone': time_zone,
                },
            }

        self.service.events().insert(calendarId=calendar_id, body=event).execute()

    def delete_events(self, events=None, calendar_name=None, calendar_id=None):
        """Delete a list of events from a Google Calendar.

        Args:
            events (list of dict): Event dicts as returned by the Calendar
                API, each containing an 'id' key.
            calendar_name (str, optional): Calendar name. Defaults to None.
            calendar_id (str, optional): Calendar ID. Defaults to None.

        Raises:
            ValueError: If calendar_name and calendar_id refer to different
                calendars.
        """
        calendar_id = self._resolve_calendar_id(calendar_name, calendar_id)
        for event in events:
            self.service.events().delete(calendarId=calendar_id, eventId=event.get('id')).execute()

    def export_to_ics(self, event, ics_path='event.ics'):
        """Convert a Google Calendar event dict to an ICS file.

        Handles both timed events ('dateTime' key) and all-day events
        ('date' key). All-day events are written with DATE values rather
        than DATE-TIME values in the ICS file, which is required for
        calendar clients to display them correctly as all-day events.

        Args:
            event (dict): A Google Calendar event dict. Required keys are
                'summary', 'start' (dict with 'dateTime' or 'date'), and
                'end' (dict with 'dateTime' or 'date'). Optional keys
                include 'description', 'location', and 'start'/'end'
                containing a 'timeZone' entry.
            ics_path (str, optional): Destination path for the ICS file.
                Defaults to 'event.ics'.

        Raises:
            KeyError: If required event keys are missing.
            ValueError: If datetime parsing fails or an invalid time zone
                is specified.
        """
        def parse_datetime_with_tz(dt, timezone_str):
            """Parse a timed datetime string and localize it to the given time zone.

            Args:
                dt (str): ISO 8601 datetime string.
                timezone_str (str): IANA time zone identifier.

            Returns:
                datetime.datetime: Timezone-aware datetime object.
            """
            dt_obj = parser.parse(dt)
            timezone = pytz.timezone(timezone_str)
            if dt_obj.tzinfo is None:
                return timezone.localize(dt_obj)
            return dt_obj

        cal = Calendar()
        cal_event = Event()

        cal_event.add('summary', event['summary'])
        cal_event.add('description', event.get('description', ''))
        cal_event.add('location', event.get('location', ''))

        # Prefer 'dateTime' (timed event); fall back to 'date' (all-day event).
        start_datetime = event['start'].get('dateTime')
        end_datetime = event['end'].get('dateTime')
        is_all_day = start_datetime is None

        if is_all_day:
            # All-day events use date objects, not datetime objects.  Using a
            # datetime here would produce a DATE-TIME value in the ICS file,
            # which most calendar clients would not treat as an all-day event.
            dtstart = parser.parse(event['start']['date']).date()
            dtend = parser.parse(event['end']['date']).date()
            cal_event.add('dtstart', dtstart)
            cal_event.add('dtend', dtend)
        else:
            timezone_str = event['start'].get('timeZone', 'UTC')
            dtstart = parse_datetime_with_tz(start_datetime, timezone_str)
            dtend = parse_datetime_with_tz(end_datetime, timezone_str)
            cal_event.add('dtstart', dtstart, parameters={'TZID': timezone_str})
            cal_event.add('dtend', dtend, parameters={'TZID': timezone_str})

        cal_event.add('dtstamp', datetime.datetime.now().astimezone(get_localzone()))

        cal.add_component(cal_event)

        with open(ics_path, 'wb') as ics_file:
            ics_file.write(cal.to_ical())

        print(f"Event exported to {ics_path} successfully.")

    def find_future_events(
        self,
        title_contains=None,
        description_contains=None,
        calendar_name=None,
        calendar_id=None,
        maxResults=1000,
    ):
        """Find future events matching a title or description keyword.

        Args:
            title_contains (str, optional): Return only events whose title
                contains this string. Defaults to None.
            description_contains (str, optional): Return only events whose
                description contains this string. Defaults to None.
            calendar_name (str, optional): Calendar to search. Defaults to
                None (uses primary calendar).
            calendar_id (str, optional): Calendar ID to search. Defaults to
                None (uses primary calendar).
            maxResults (int, optional): Maximum number of results to fetch
                from the API before filtering. Defaults to 1000.

        Returns:
            list of dict: Matching future event dicts. Returns all future
                events if no filter is specified.

        Raises:
            ValueError: If calendar_name and calendar_id refer to different
                calendars.
        """
        calendar_id = self._resolve_calendar_id(calendar_name, calendar_id)

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        all_events = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=maxResults,
                singleEvents=True,
                orderBy='startTime',
            )
            .execute()
            .get('items', [])
        )

        if title_contains is None and description_contains is None:
            return all_events

        events = []
        for event in all_events:
            summary = event.get('summary', '')
            description = event.get('description', '')
            title_match = title_contains is None or title_contains in summary
            desc_match = description_contains is None or description_contains in description
            if title_match and desc_match:
                events.append(event)

        return events

    def import_from_ics(self, ics_path=None, calendar_name=None, calendar_id=None, delete_ics=False):
        """Import events from an ICS file into a Google Calendar.

        Args:
            ics_path (str, optional): Path to the .ics file. Defaults to
                None.
            calendar_name (str, optional): Target calendar name. Defaults
                to None (uses primary calendar).
            calendar_id (str, optional): Target calendar ID. Defaults to
                None (uses primary calendar).
            delete_ics (bool, optional): If True, delete the .ics file
                after a successful import. Defaults to False.

        Raises:
            FileNotFoundError: If ics_path does not exist.
            ValueError: If the ICS file cannot be parsed, or if
                calendar_name and calendar_id refer to different calendars.
        """
        if not ics_path or not os.path.exists(ics_path):
            raise FileNotFoundError(f"ICS file not found: {ics_path}")

        calendar_id = self._resolve_calendar_id(calendar_name, calendar_id)

        try:
            events = self.parse_ics(ics_path)
        except Exception as e:
            raise ValueError(f"Failed to parse ICS file: {e}") from e

        for event in events:
            print(f"Importing event: {event.get('summary', 'Unnamed Event')}")
            print(f"Start: {event.get('start')}")
            print(f"End: {event.get('end')}")
            try:
                self.service.events().insert(calendarId=calendar_id, body=event).execute()
            except Exception as e:
                print(f"Failed to import event: {event.get('summary', 'Unnamed Event')} - {e}")

        if delete_ics:
            try:
                os.remove(ics_path)
            except OSError as e:
                print(f"Failed to delete ICS file: {ics_path} - {e}")

    def make_multiple_events(
        self,
        title='Event',
        description=None,
        start_date=None,
        end_date=None,
        event_time=None,
        duration=None,
        duration_units='H',
        freq='B',
        periods=None,
        calendar_name=None,
        calendar_id=None,
        time_zone=None,
    ):
        """Create multiple recurring events in a Google Calendar.

        Args:
            title (str, optional): Event title. Defaults to 'Event'.
            description (str, optional): Event description. Defaults to
                None.
            start_date (str): Start of the recurring series. Accepts
                natural-language strings parsed by pandas.
            end_date (str, optional): End of the recurring series.
                Defaults to None.
            event_time (str, optional): Time-of-day to append to
                start_date when generating the date range. Defaults to
                None.
            duration (float, optional): Duration of each event in
                ``duration_units``. Defaults to None.
            duration_units (str, optional): Pandas offset alias for the
                duration unit. Defaults to 'H'.
            freq (str, optional): Recurrence frequency as a pandas offset
                alias (e.g., 'B' for business days). Defaults to 'B'.
            periods (int, optional): Number of occurrences to generate.
                Defaults to None.
            calendar_name (str, optional): Target calendar name. Defaults
                to None.
            calendar_id (str, optional): Target calendar ID. Defaults to
                None.
            time_zone (str, optional): IANA time zone identifier. Defaults
                to None.
        """
        if event_time is not None:
            start_date = start_date + ' ' + event_time

        dates = pd.date_range(
            start=start_date, end=end_date, periods=periods, freq=freq, tz=time_zone
        )
        ending_dates = dates + pd.Timedelta(duration, unit=duration_units)

        for n, time in enumerate(dates):
            self.add_event(
                start=time,
                end=ending_dates[n],
                duration=duration,
                title=title,
                description=description,
                calendar_name=calendar_name,
                calendar_id=calendar_id,
                time_zone=time_zone,
            )

    def parse_ics(self, ics_path):
        """Parse an ICS file into a list of Google Calendar event dicts.

        Args:
            ics_path (str): Path to the .ics file.

        Returns:
            list of dict: One dict per VEVENT component found in the file.
                Each dict may contain 'summary', 'location', 'description',
                'start' (dict with 'dateTime' and 'timeZone'), and 'end'
                (dict with 'dateTime' and 'timeZone'). Events missing
                'start' or 'end' are silently skipped.

        Raises:
            FileNotFoundError: If ics_path does not exist.
            ValueError: If the file contains malformed ICS data.
        """
        def parse_datetime(prop):
            """Parse a vcalendar datetime property into an API-compatible dict.

            Args:
                prop: An icalendar property object with a .dt attribute.

            Returns:
                dict: Dict with 'dateTime' (ISO 8601 str) and 'timeZone'
                    (str) keys.
            """
            dt = prop.dt
            if not isinstance(dt, datetime.datetime):
                dt = parser.parse(str(dt))
            tzinfo = dt.tzinfo or pytz.UTC
            return {
                'dateTime': dt.isoformat(),
                'timeZone': str(tzinfo.zone) if hasattr(tzinfo, 'zone') else 'UTC',
            }

        events = []
        with open(ics_path, 'r', encoding='utf-8') as rf:
            ical = Calendar.from_ical(rf.read())
            for comp in ical.walk():
                if comp.name == 'VEVENT':
                    event = {}
                    for name, prop in comp.property_items():
                        if name == 'SUMMARY':
                            # Convert icalendar property objects to plain strings;
                            # the Google Calendar API expects str, not vText.
                            event['summary'] = str(prop)
                        elif name == 'LOCATION':
                            event['location'] = str(prop)
                        elif name == 'DTSTART':
                            event['start'] = parse_datetime(prop)
                        elif name == 'DTEND':
                            event['end'] = parse_datetime(prop)
                        elif name == 'DESCRIPTION':
                            event['description'] = str(prop)

                    if 'start' in event and 'end' in event:
                        events.append(event)

        return events
