``google`` module
=================

.. py:module:: google
   :synopsis: Module for interacting with Gmail and the Google API.

Functions
---------

.. py:function:: authenticate_google_app(
      credentials_path='gmail_credentials.json', 
      token_path='gmail_token.json', 
      SCOPES=None, 
      service_name=None, 
      service_version=None)

   Authenticates and initializes a Google API service.

   :param str credentials_path: 
      Path to the credentials file for the Google API.
   :param str token_path: 
      Path to the token file for storing user authentication.
   :param list SCOPES: 
      List of scopes for the Google API service.
   :param str service_name: 
      Name of the Google API service (e.g., 'gmail', 'calendar').
   :param str service_version: 
      Version of the Google API service (e.g., 'v1', 'v3').
   :return: Authenticated Google API service object.
   :rtype: googleapiclient.discovery.Resource

Classes
-------

.. py:class:: gmail(
      credentials_path='credentials.json', 
      token_path='token.json', 
      sender=None)

   A class for managing Gmail messages using the Google API.

   :param str credentials_path: 
      Path to the Google API credentials file. Default is 'credentials.json'.
   :param str token_path: 
      Path to the token file for authentication. Default is 'token.json'.
   :param str sender: 
      Default sender email address. Default is None.

   **Methods**

   .. py:method:: add_message_label(
         message=None, 
         message_id=None, 
         label_names=None, 
         label_ids=None)

      Adds one or more labels to a Gmail message.

      :param dict message: 
         Message metadata dictionary. Default is None.
      :param str message_id: 
         ID of the message to label.
      :param str or list label_names: 
         Name(s) of the label(s) to add.
      :param str or list label_ids: 
         ID(s) of the label(s) to add.
      :return: None

   .. py:method:: delete_message(
         message=None, 
         message_id=None)

      Permanently deletes a Gmail message.

      :param dict message: 
         Message metadata dictionary. Default is None.
      :param str message_id: 
         ID of the message to delete.
      :return: None

   .. py:method:: get_all_labels()

      Retrieves all Gmail labels for the user.

      :return: DataFrame containing label names and metadata.
      :rtype: pandas.DataFrame

   .. py:method:: get_from_sender(
         sender, 
         label_name=None, 
         label_id=None)

      Finds all messages from a specific sender.

      :param str sender: 
         Email address of the sender to search for.
      :param str label_name: 
         Name of the Gmail label to filter messages by. Default is None.
      :param str label_id: 
         ID of the Gmail label to filter messages by. Default is None.
      :return: List of message metadata dictionaries.
      :rtype: list

   .. py:method:: make_message(
         sender=None, 
         to=None, 
         cc=None, 
         bcc=None, 
         subject='No subject', 
         plain_text=None, 
         html_text=None, 
         markdown_text=None, 
         send=True, 
         attachments=None)

      Creates and optionally sends a Gmail message.

      :param str sender: 
         Email address of the sender. Default is None.
      :param str or list to: 
         Recipient email address(es). Default is None.
      :param str cc: 
         CC email address(es). Default is None.
      :param str bcc: 
         BCC email address(es). Default is None.
      :param str subject: 
         Email subject. Default is 'No subject'.
      :param str plain_text: 
         Plain text content of the email. Default is None.
      :param str html_text: 
         HTML content of the email. Default is None.
      :param str markdown_text: 
         Markdown content for the email. Default is None.
      :param bool send: 
         Whether to send the email immediately. Default is True.
      :param str or list attachments: 
         Path(s) to attachment files. Default is None.
      :return: Sent message metadata if `send=True`, else draft metadata.
      :rtype: dict

   .. py:method:: trash_message(
         message=None, 
         message_id=None)

      Moves a Gmail message to the trash.

      :param dict message: 
         Message metadata dictionary. Default is None.
      :param str message_id: 
         ID of the message to delete. Default is None.
      :return: None

   .. py:method:: move_message(
         message=None, 
         message_id=None, 
         old_label_name=None, 
         new_label_name=None)

      Moves a Gmail message from one label to another.

      :param dict message: 
         Message metadata dictionary. Default is None.
      :param str message_id: 
         ID of the message to move. Default is None.
      :param str old_label_name: 
         Name of the current label.
      :param str new_label_name: 
         Name of the target label.
      :return: None

.. py:class:: calendar(
      credentials_path='credentials.json', 
      token_path='token.json')

   Class for interacting with Google Calendar. This class provides methods to manage calendars, add events, import/export events, and parse `.ics` files.

   :param str credentials_path: 
      Path to the Google Calendar credentials file. Default is 'credentials.json'.
   :param str token_path: 
      Path to the token file for authentication. Default is 'token.json'.

   **Methods**

   .. py:method:: add_event(
         start, 
         end=None, 
         duration=0, 
         duration_units='H', 
         title='Event', 
         description=None, 
         calendar_name=None, 
         calendar_id=None, 
         time_zone=None)

      Adds a single event to a Google Calendar.

      :param str start: 
         Start time of the event (e.g., "January 4, 2022 4pm").
      :param str end: 
         End time of the event. Default is None.
      :param float duration: 
         Duration of the event in units specified by `duration_units`. Default is 0.
      :param str duration_units: 
         Units for event duration (e.g., 'H' for hours). Default is 'H'.
      :param str title: 
         Title of the event. Default is 'Event'.
      :param str description: 
         Description of the event. Default is None.
      :param str calendar_name: 
         Name of the calendar to add the event to. Default is None.
      :param str calendar_id: 
         ID of the calendar to add the event to. Default is None.
      :param str time_zone: 
         Time zone of the event (e.g., "America/New_York"). Default is None.
      :raises ValueError: 
         If `calendar_name` and `calendar_id` do not reference the same calendar.
      :return: None

   .. py:method:: delete_events(
         events=None, 
         calendar_name=None, 
         calendar_id=None)

      Deletes events from a Google Calendar.

      :param list events: 
         List of event dictionaries to delete.
      :param str calendar_name: 
         Name of the calendar containing the events. Default is None.
      :param str calendar_id: 
         ID of the calendar containing the events. Default is None.
      :raises ValueError: 
         If `calendar_name` and `calendar_id` do not reference the same calendar.
      :return: None

   .. py:method:: export_to_ics(
         event, 
         ics_path='event.ics')

      Exports a Google Calendar event to an ICS file format.

      :param dict event: 
         Dictionary representing a Google Calendar event.
      :param str ics_path: 
         File path to save the ICS file. Default is 'event.ics'.
      :raises KeyError: 
         If required keys ('summary', 'start', 'end') are missing in the event.
      :raises ValueError: 
         If datetime parsing fails or an invalid timezone is specified.
      :return: None