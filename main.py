import datetime
import email
import email.utils
import imaplib
import os
from email.header import decode_header
from typing import Union

from rich import print

from secret import account_email, account_password, host
from src.utils import status

DIR_BACKUP = 'backup'

def get_email_content(msg) -> Union[bytes, str, None]:
    html = None
    plain_text = None
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/html" and "attachment" not in content_disposition:
                html = part.get_payload(decode=True)
            elif content_type == "text/plain" and "attachment" not in content_disposition:
                plain_text = part.get_payload(decode=True)
    else:
        # For non-multipart emails, directly get the payload
        content_type = msg.get_content_type()
        if content_type == "text/html":
            html = msg.get_payload(decode=True)
        elif content_type == "text/plain":
            plain_text = msg.get_payload(decode=True)
    
    # Prefer HTML content if available; otherwise, return plain text
    return html if html is not None else plain_text


def connect_to_server(imap_host, user, password) -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(user, password)
    return mail

def search_emails(mail) -> list:
    mail.select('inbox')  # Select the mailbox you want to back up
    status, messages = mail.search(None, 'ALL')
    return messages[0].split(b' ')

def save_email(email_message, email_num: int):
    # Extract date and format it
    date_tuple = email.utils.parsedate_tz(email_message['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        formatted_date = local_date.strftime('%Y-%m-%d %H:%M')
    else:
        formatted_date = 'unknown_date'

    # Extract sender
    sender = email_message.get('From', 'unknown_sender')
    sender_email = email.utils.parseaddr(sender)[1]

    # Decode subject
    subject = decode_header(email_message['Subject'])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode(errors='ignore')
    filename_safe_subject = "".join(i for i in subject if i not in "\/:*?<>|")

    # Create a unique directory for each email based on date, sender, and subject
    email_dir_name = f"{formatted_date} - {sender_email} - {filename_safe_subject}"
    email_dir = os.path.join(DIR_BACKUP, email_dir_name)
    os.makedirs(email_dir, exist_ok=True)

    # Save the email body
    for part in email_message.walk():
        content_disposition = str(part.get("Content-Disposition"))
        content_type = part.get_content_type()
        if content_disposition.startswith('attachment'):
            attachment_filename = part.get_filename()
            if attachment_filename:
                attachment_filename = decode_header(attachment_filename)[0][0]
                if isinstance(attachment_filename, bytes):
                    attachment_filename = attachment_filename.decode()
                attachment_path = os.path.join(email_dir, attachment_filename)
                # Save attachment
                with open(attachment_path, 'wb') as f:
                    f.write(part.get_payload(decode=True))
        elif content_type in ['text/plain', 'text/html']:
            content = part.get_payload(decode=True)
            if content_type == 'text/plain':
                content = content.decode('utf-8', errors='ignore')
                content = f"<html><body><pre>{content}</pre></body></html>"
                content = content.encode('utf-8')
            filename = os.path.join(email_dir, 'email_content.html')
            with open(filename, 'wb') as f:
                f.write(content)

    print(f'Saved email and attachments to: {email_dir}')




def main():
    # Create a directory for emails if it doesn't exist
    if not os.path.exists(DIR_BACKUP):
        os.makedirs(DIR_BACKUP)

    # Login to IMAP server
    mail = connect_to_server(host, account_email, account_password)

    # Search for all emails in the inbox
    messages = search_emails(mail)

    for num, mail_id in enumerate(messages, 1):
        status, data = mail.fetch(mail_id, '(BODY.PEEK[])')
        raw_email = data[0][1]

        email_message = email.message_from_bytes(raw_email)
        save_email(email_message, num)

    # Logout
    mail.logout()

if __name__ == "__main__":
    main()
