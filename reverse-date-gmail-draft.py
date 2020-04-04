from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import email
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import os
from apiclient import errors

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

def CreateDraft(service, user_id, message_body):
    message = {'message': message_body}
    draft = service.users().drafts().create(userId=user_id, body=message).execute()
    return draft

def CreateMessage(sender, to, subject, message_text):
  """Create a message for an email.

  Args:
    sender: Email address of the sender.
    to: Email address of the receiver.
    subject: The subject of the email message.
    message_text: The text of the email message.

  Returns:
    An object containing a base64url encoded email object.
  """
  message = MIMEText(message_text)
  message['to'] = to
  message['from'] = sender
  message['subject'] = subject
  b64 = base64.urlsafe_b64encode(message.as_string().encode('utf-8')).decode('utf-8')
  return {'raw': b64}

def reverse_date_format_text(text):
    words = text.split()
    dates_string = []
    #recieve dates old and new
    for word in words:
        word_set = set(word)
        date_set = set('.0123456789')
        if word_set.issubset(date_set):
            dates_string.append(word)
    for date_string in dates_string:
        a = [s for s in date_string.split('.')]        
        b = a[::-1]
        result = ''
        for s in b:
            result += s + '.'
            date_new_string = result[0:-1]            
        text = text.replace(date_string,result[0:-1])
    return text      
            

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    #Recieve all drafts
    results = service.users().drafts().list(userId='me').execute()

    #Extract first draft id
    draft_old_id = results['drafts'][0]['id']

    #Getting draft text data
    draft = service.users().drafts().get(userId='me', id=draft_old_id).execute()

    #b64 to string
    msg_str = base64.urlsafe_b64decode(draft['message']['payload']['body']['data'])
    draft_text = msg_str.decode('utf-8')

    #reverse dates in text of first draft
    draft_text_new = reverse_date_format_text(draft_text)

    #creating new draft
    sender, to, subject = [''] * 3
    for header in draft['message']['payload']['headers']:
        if header['name'] == 'To':
            to = header['value']
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'From':
            sender = header['value']
    new_message = CreateMessage(sender, to, subject, draft_text_new)
    CreateDraft(service, 'me', new_message)
    
    #deleting old draft
    service.users().drafts().delete(userId='me', id=draft_old_id).execute()    

if __name__ == '__main__':
    main()
