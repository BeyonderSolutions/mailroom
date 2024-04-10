import email
import imaplib
import os
from email.header import decode_header
from typing import Union
from rich import print

from secret import account_email, account_password, host
from src.utils import status

DIR_BACKUP = 'backup'

def get_html_part(msg) -> Union[bytes, None]:
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/html" and "attachment" not in content_disposition:
                return part.get_payload(decode=True)
    else:
        if msg.get_content_type() == "text/html":
            return msg.get_payload(decode=True)
    return None

def connect_to_server(imap_host, user, password) -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(user, password)
    return mail

def search_emails(mail) -> list:
    mail.select('inbox')  # Select the mailbox you want to back up
    status, messages = mail.search(None, 'ALL')
    return messages[0].split(b' ')

def save_email(html_part: bytes, subject: str, email_num: int):
    filename_safe_subject = "".join(i for i in subject if i not in "\/:*?<>|")
    filename = os.path.join(DIR_BACKUP, f"email_{email_num}_{filename_safe_subject}.html")
    with open(filename, 'wb') as f:
        f.write(html_part)
    print(f'Saved: {filename}')

def main():
    # Create a directory for emails if it doesn't exist
    if not os.path.exists(DIR_BACKUP):
        os.makedirs(DIR_BACKUP)

    # Login to IMAP server
    mail = connect_to_server(host, account_email, account_password)

    # Search for all emails in the inbox
    messages = search_emails(mail)

    for num, mail_id in enumerate(messages, 1):
        # Use the PEEK command to fetch the email without marking it as read
        status, data = mail.fetch(mail_id, '(BODY.PEEK[])')  # Updated line here
        raw_email = data[0][1]

        email_message = email.message_from_bytes(raw_email)
        html_part = get_html_part(email_message)

        if html_part:
            subject = decode_header(email_message['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            save_email(html_part, subject, num)
        else:
            print(f'No HTML content: email_{num}')

    # Logout
    mail.logout()

if __name__ == "__main__":
    main()
