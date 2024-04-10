import datetime
import email
import email.utils
import imaplib
import json
import os
from email.header import decode_header
from typing import Union

from rich import print
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
    if status != 'OK':
        print("No messages found!")
        return []
    message_list = messages[0].split(b' ')
    if message_list == [b'']:
        return []
    return message_list

def save_email(email_message, email_num: int, backup_dir: str):
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
    email_dir = os.path.join(backup_dir, email_dir_name)
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
    # Load the configuration from config.json
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    for account in config['accounts']:
        host = account['host']
        user_email = account['email']
        user_password = account['password']

        # Create a backup directory specific to the account
        backup_dir = os.path.join(DIR_BACKUP, user_email)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Login to IMAP server for the current account
        mail = connect_to_server(host, user_email, user_password)

        # Search for all emails in the inbox
        messages = search_emails(mail)
        if not messages:
            print(f"No messages to fetch for {user_email}")
            continue

        for num, mail_id in enumerate(messages, 1):
            try:
                status, data = mail.fetch(mail_id, '(BODY.PEEK[])')
                if status != 'OK':
                    print(f"Failed to fetch email with ID {mail_id.decode()}")
                    continue
                raw_email = data[0][1]

                email_message = email.message_from_bytes(raw_email)
                save_email(email_message, num, backup_dir)  # Pass the backup directory to the save_email function
            except imaplib.IMAP4.error as e:
                print(f"An error occurred while fetching email with ID {mail_id.decode()}: {e}")


        # Logout
        mail.logout()

        print(f'Finished backup for account: {user_email}')


if __name__ == "__main__":
    main()
