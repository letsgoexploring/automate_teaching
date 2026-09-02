``google_api`` module
=====================

.. py:module:: google_api
   :synopsis: Provides classes for interacting with Gmail and Google Calendar via the Google API.

Functions
---------

.. py:function:: authenticate_google_app(credentials_path='gmail_credentials.json', token_path='gmail_token.json', SCOPES=None, service_name=None, service_version=None)

   Authenticates and returns a Google API service object. Reads cached
   credentials from ``token_path`` if available. When a cached token exists
   but has expired, it is refreshed silently using the stored refresh token.
   Only when no valid token exists at all is the full OAuth browser flow
   triggered. The (potentially refreshed) token is always written back to
   ``token_path`` so subsequent calls can reuse it.

   :param credentials_path: Path to the OAuth client secrets file downloaded
      from the Google Cloud console. Defaults to ``'gmail_credentials.json'``.
   :type credentials_path: str, optional
   :param token_path: Path where the user token is cached. Defaults to
      ``'gmail_token.json'``.
   :type token_path: str, optional
   :param SCOPES: OAuth scopes to request. Defaults to None.
   :type SCOPES: list of str, optional
   :param service_name: Google API service identifier (e.g., ``'gmail'``,
      ``'calendar'``). Defaults to None.
   :type service_name: str, optional
   :param service_version: API version string (e.g., ``'v1'``, ``'v3'``).
      Defaults to None.
   :type service_version: str, optional
   :return: Authenticated Google API service object.
   :rtype: googleapiclient.discovery.Resource

Classes
-------

.. py:class:: Gmail(credentials_path='credentials.json', token_path='token.json', sender=None)

   Manages and sends Gmail messages via the Gmail API.

   :param credentials_path: Path to the Google API OAuth credentials file.
      Defaults to ``'credentials.json'``.
   :type credentials_path: str, optional
   :param token_path: Path to the cached token file. Defaults to
      ``'token.json'``.
   :type token_path: str, optional
   :param sender: Default sender email address used when no sender is
      specified in ``make_message``. Defaults to None.
   :type sender: str, optional

   .. py:method:: add_message_label(message=None, message_id=None, label_names=None, label_ids=None)

      Adds one or more labels to a Gmail message.

      :param message: Message metadata dict containing an ``'id'`` key. Used
         when ``message_id`` is not provided. Defaults to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :param label_names: Label name(s) to add. Accepts a single string or a
         list of strings. Defaults to None.
      :type label_names: str or list of str, optional
      :param label_ids: Label ID(s) to add. Takes precedence over
         ``label_names`` if both are provided. Defaults to None.
      :type label_ids: str or list of str, optional
      :return: None

   .. py:method:: delete_message(message=None, message_id=None)

      Permanently deletes a Gmail message.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :return: None

   .. py:method:: get_all_labels()

      Retrieves all Gmail labels for the authenticated account.

      :return: DataFrame with one row per label, containing label names and
         metadata returned by the API.
      :rtype: pandas.DataFrame

   .. py:method:: get_from_sender(sender, label_name=None, label_id=None)

      Finds all messages from a specific sender. When ``label_name`` is
      provided it is resolved to a label ID via ``get_label_id``.

      :param sender: Email address of the sender to search for.
      :type sender: str
      :param label_name: Filter by this label name. Defaults to None.
      :type label_name: str, optional
      :param label_id: Filter by this label ID directly. Takes precedence
         over ``label_name`` if both are provided. Defaults to None.
      :type label_id: str, optional
      :return: List of message metadata dicts, or None if no messages are
         found.
      :rtype: list of dict or None

   .. py:method:: get_label_id(label_name)

      Returns the ID of a Gmail label by its display name.

      :param label_name: The exact label name (case-insensitive).
      :type label_name: str
      :return: The label ID, or None if no matching label is found.
      :rtype: str or None

   .. py:method:: get_labeled_messages(label_name=None, label_id=None)

      Retrieves all messages with a specific label. When ``label_name`` is
      provided it is resolved to a label ID via ``get_label_id``.

      :param label_name: Label name to filter by. Defaults to None.
      :type label_name: str, optional
      :param label_id: Label ID to filter by directly. Takes precedence over
         ``label_name`` if both are provided. Defaults to None.
      :type label_id: str, optional
      :return: List of message metadata dicts, or None if no messages are
         found.
      :rtype: list of dict or None

   .. py:method:: get_message(message=None, message_id=None)

      Retrieves a full Gmail message by its ID.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :return: Full Gmail message payload returned by the API.
      :rtype: dict

   .. py:method:: get_message_return_path(message=None, message_id=None)

      Returns the ``Return-Path`` (or ``From``) address of a message.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :return: The sender email address extracted from the Return-Path or
         From header.
      :rtype: str

   .. py:method:: get_return_paths(messages=None)

      Returns the sender address for each message in a list.

      :param messages: List of message metadata dicts, each containing an
         ``'id'`` key.
      :type messages: list of dict
      :return: Return-Path or From addresses, one per message.
      :rtype: list of str

   .. py:method:: make_message(sender=None, to=None, cc=None, bcc=None, subject='No subject', plain_text=None, html_text=None, markdown_text=None, send=True, attachments=None)

      Creates and optionally sends a Gmail message. At least one of
      ``plain_text``, ``html_text``, or ``markdown_text`` should be provided.
      Markdown is converted to HTML before sending. If none is provided, the
      body defaults to ``'No message'``.

      :param sender: Sender email address. Falls back to ``self.sender`` if
         not provided. Defaults to None.
      :type sender: str, optional
      :param to: Recipient address(es). Defaults to None.
      :type to: str or list of str, optional
      :param cc: CC address(es). Defaults to None.
      :type cc: str or list of str, optional
      :param bcc: BCC address(es). Defaults to None.
      :type bcc: str or list of str, optional
      :param subject: Email subject line. Defaults to ``'No subject'``.
      :type subject: str, optional
      :param plain_text: Plain-text email body. Defaults to None.
      :type plain_text: str, optional
      :param html_text: HTML email body. Defaults to None.
      :type html_text: str, optional
      :param markdown_text: Markdown email body (converted to HTML). Defaults
         to None.
      :type markdown_text: str, optional
      :param send: If True, send immediately; if False, save as a draft.
         Defaults to True.
      :type send: bool, optional
      :param attachments: File path(s) to attach. Defaults to None.
      :type attachments: str or list of str, optional
      :return: Sent message metadata if ``send=True``, draft metadata if
         ``send=False``, or None if an HTTP error occurs.
      :rtype: dict or None

   .. py:method:: move_message(message=None, message_id=None, old_label_name=None, new_label_name=None)

      Moves a Gmail message from one label to another. Only the labels that
      are actually specified are sent to the API, so passing only
      ``new_label_name`` adds a label without removing one, and passing only
      ``old_label_name`` removes a label without adding one.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :param old_label_name: Label to remove. Defaults to None.
      :type old_label_name: str, optional
      :param new_label_name: Label to add. Defaults to None.
      :type new_label_name: str, optional
      :return: None

   .. py:method:: move_messages(messages=None, old_label_name=None, new_label_name=None)

      Moves a list of Gmail messages from one label to another by calling
      ``move_message`` for each message.

      :param messages: List of message metadata dicts, each with an ``'id'``
         key.
      :type messages: list of dict
      :param old_label_name: Label to remove from each message. Defaults to
         None.
      :type old_label_name: str, optional
      :param new_label_name: Label to add to each message. Defaults to None.
      :type new_label_name: str, optional
      :return: None

   .. py:method:: remove_message_label(message=None, message_id=None, label_names=None, label_ids=None)

      Removes one or more labels from a Gmail message.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :param label_names: Label name(s) to remove. Accepts a single string
         or a list. Defaults to None.
      :type label_names: str or list of str, optional
      :param label_ids: Label ID(s) to remove. Defaults to None.
      :type label_ids: str or list of str, optional
      :return: None

   .. py:method:: trash_message(message=None, message_id=None)

      Moves a Gmail message to the trash.

      :param message: Message metadata dict with an ``'id'`` key. Defaults
         to None.
      :type message: dict, optional
      :param message_id: Gmail message ID. Defaults to None.
      :type message_id: str, optional
      :return: None


.. py:class:: GoogleCalendar(credentials_path='credentials.json', token_path='token.json')

   Interacts with Google Calendar via the Calendar API. On initialization,
   retrieves the list of all calendars and identifies the primary calendar.

   :param credentials_path: Path to the OAuth client secrets file. Defaults
      to ``'credentials.json'``.
   :type credentials_path: str, optional
   :param token_path: Path to the cached token file. Defaults to
      ``'token.json'``.
   :type token_path: str, optional

   .. py:attribute:: calendar_ids
      :type: pandas.Series

      Series mapping calendar display names to their calendar IDs.

   .. py:attribute:: primary_calendar
      :type: str

      Display name of the authenticated user's primary calendar.

   .. py:attribute:: primary_calendar_id
      :type: str

      Calendar ID of the primary calendar.

   .. py:method:: add_event(start, end=None, duration=0, duration_units='H', title='Event', description=None, calendar_name=None, calendar_id=None, time_zone=None, all_day=False)

      Adds a single event to a Google Calendar.

      :param start: Event start time. Accepts natural-language strings parsed
         by pandas (e.g., ``'January 4, 2022 4pm'``).
      :type start: str
      :param end: Event end time. Defaults to None, in which case
         ``duration`` is used.
      :type end: str, optional
      :param duration: Duration of the event in ``duration_units``. Ignored
         when ``end`` is provided. Defaults to 0.
      :type duration: float, optional
      :param duration_units: Pandas offset alias for the duration unit
         (e.g., ``'H'`` for hours). Defaults to ``'H'``.
      :type duration_units: str, optional
      :param title: Event title. Defaults to ``'Event'``.
      :type title: str, optional
      :param description: Event description. Defaults to None.
      :type description: str, optional
      :param calendar_name: Target calendar name. Defaults to None (uses
         primary calendar).
      :type calendar_name: str, optional
      :param calendar_id: Target calendar ID. Defaults to None (uses primary
         calendar).
      :type calendar_id: str, optional
      :param time_zone: IANA time zone identifier (e.g.,
         ``'America/Los_Angeles'``). Defaults to None, which uses the
         calendar's own time zone.
      :type time_zone: str, optional
      :param all_day: If True, create an all-day event. Defaults to False.
      :type all_day: bool, optional
      :raises ValueError: If ``calendar_name`` and ``calendar_id`` refer to
         different calendars.
      :return: None

   .. py:method:: delete_events(events=None, calendar_name=None, calendar_id=None)

      Deletes a list of events from a Google Calendar.

      :param events: Event dicts as returned by the Calendar API, each
         containing an ``'id'`` key.
      :type events: list of dict
      :param calendar_name: Calendar name. Defaults to None (uses primary
         calendar).
      :type calendar_name: str, optional
      :param calendar_id: Calendar ID. Defaults to None (uses primary
         calendar).
      :type calendar_id: str, optional
      :raises ValueError: If ``calendar_name`` and ``calendar_id`` refer to
         different calendars.
      :return: None

   .. py:method:: export_to_ics(event, ics_path='event.ics')

      Converts a Google Calendar event dict to an ICS file. Handles both
      timed events (``'dateTime'`` key) and all-day events (``'date'`` key).
      All-day events are written with ``DATE`` values rather than
      ``DATE-TIME`` values, which is required for calendar clients to display
      them correctly.

      :param event: A Google Calendar event dict. Required keys are
         ``'summary'``, ``'start'`` (dict with ``'dateTime'`` or ``'date'``),
         and ``'end'`` (dict with ``'dateTime'`` or ``'date'``). Optional
         keys include ``'description'``, ``'location'``, and a ``'timeZone'``
         entry inside ``'start'``/``'end'``.
      :type event: dict
      :param ics_path: Destination path for the ICS file. Defaults to
         ``'event.ics'``.
      :type ics_path: str, optional
      :raises KeyError: If required event keys are missing.
      :raises ValueError: If datetime parsing fails or an invalid time zone
         is specified.
      :return: None

   .. py:method:: find_events(title_contains=None, description_contains=None, calendar_name=None, calendar_id=None, maxResults=1000, direction='future')

      Finds events matching a title or description keyword.

      :param title_contains: Return only events whose title contains this
         string. Defaults to None.
      :type title_contains: str, optional
      :param description_contains: Return only events whose description
         contains this string. Defaults to None.
      :type description_contains: str, optional
      :param calendar_name: Calendar to search. Defaults to None (uses
         primary calendar).
      :type calendar_name: str, optional
      :param calendar_id: Calendar ID to search. Defaults to None (uses
         primary calendar).
      :type calendar_id: str, optional
      :param maxResults: Maximum number of results to fetch from the API
         before filtering. Defaults to 1000.
      :type maxResults: int, optional
      :param direction: Which events (relative to now) to search.

         - ``'future'`` — only events starting now or later.
         - ``'past'`` — only events starting before now.
         - ``'all'`` — every event on the calendar, regardless of start
           time.

         Defaults to ``'future'``.
      :type direction: str, optional
      :return: Matching event dicts. Returns all events in the searched
         range if no title/description filter is specified.
      :rtype: list of dict
      :raises ValueError: If ``calendar_name`` and ``calendar_id`` refer to
         different calendars, or if ``direction`` is not one of
         ``'future'``, ``'past'``, or ``'all'``.

   .. py:method:: import_from_ics(ics_path=None, calendar_name=None, calendar_id=None, delete_ics=False)

      Imports events from an ICS file into a Google Calendar.

      :param ics_path: Path to the ``.ics`` file. Defaults to None.
      :type ics_path: str, optional
      :param calendar_name: Target calendar name. Defaults to None (uses
         primary calendar).
      :type calendar_name: str, optional
      :param calendar_id: Target calendar ID. Defaults to None (uses primary
         calendar).
      :type calendar_id: str, optional
      :param delete_ics: If True, delete the ``.ics`` file after a successful
         import. Defaults to False.
      :type delete_ics: bool, optional
      :raises FileNotFoundError: If ``ics_path`` does not exist.
      :raises ValueError: If the ICS file cannot be parsed, or if
         ``calendar_name`` and ``calendar_id`` refer to different calendars.
      :return: None

   .. py:method:: make_multiple_events(title='Event', description=None, start_date=None, end_date=None, event_time=None, duration=None, duration_units='H', freq='B', periods=None, calendar_name=None, calendar_id=None, time_zone=None)

      Creates multiple recurring events in a Google Calendar by generating a
      date range and calling ``add_event`` for each date.

      :param title: Event title. Defaults to ``'Event'``.
      :type title: str, optional
      :param description: Event description. Defaults to None.
      :type description: str, optional
      :param start_date: Start of the recurring series. Accepts
         natural-language strings parsed by pandas.
      :type start_date: str
      :param end_date: End of the recurring series. Defaults to None.
      :type end_date: str, optional
      :param event_time: Time-of-day to append to ``start_date`` when
         generating the date range. Defaults to None.
      :type event_time: str, optional
      :param duration: Duration of each event in ``duration_units``. Defaults
         to None.
      :type duration: float, optional
      :param duration_units: Pandas offset alias for the duration unit.
         Defaults to ``'H'``.
      :type duration_units: str, optional
      :param freq: Recurrence frequency as a pandas offset alias (e.g.,
         ``'B'`` for business days). Defaults to ``'B'``.
      :type freq: str, optional
      :param periods: Number of occurrences to generate. Defaults to None.
      :type periods: int, optional
      :param calendar_name: Target calendar name. Defaults to None.
      :type calendar_name: str, optional
      :param calendar_id: Target calendar ID. Defaults to None.
      :type calendar_id: str, optional
      :param time_zone: IANA time zone identifier. Defaults to None.
      :type time_zone: str, optional
      :return: None

   .. py:method:: parse_ics(ics_path)

      Parses an ICS file into a list of Google Calendar event dicts. Text
      fields (``summary``, ``location``, ``description``) are returned as
      plain Python strings. Events missing a ``start`` or ``end`` field are
      silently skipped.

      :param ics_path: Path to the ``.ics`` file.
      :type ics_path: str
      :return: One dict per ``VEVENT`` component found in the file. Each dict
         may contain ``'summary'``, ``'location'``, ``'description'``,
         ``'start'`` (dict with ``'dateTime'`` and ``'timeZone'``), and
         ``'end'`` (dict with ``'dateTime'`` and ``'timeZone'``).
      :rtype: list of dict
      :raises FileNotFoundError: If ``ics_path`` does not exist.
      :raises ValueError: If the file contains malformed ICS data.
