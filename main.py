import email
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

def save_email(content: bytes, subject: str, email_num: int, is_html: bool):
    filename_safe_subject = "".join(i for i in subject if i not in "\/:*?<>|")
    filename = os.path.join(DIR_BACKUP, f"email_{email_num}_{filename_safe_subject}.html")

    # Attempt to decode content with utf-8, fallback to latin-1 if utf-8 decoding fails
    try:
        content_str = content.decode('utf-8')
    except UnicodeDecodeError:
        content_str = content.decode('latin-1')

    if not is_html:
        # Convert plain text newlines to <br> tags for HTML
        content_str = content_str.replace('\r\n', '<br>').replace('\n', '<br>').replace('\r', '<br>')
        # Wrap plain text in HTML tags
        content_str = f"<html><body><pre>{content_str}</pre></body></html>"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content_str)

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
        status, data = mail.fetch(mail_id, '(BODY.PEEK[])')
        raw_email = data[0][1]

        email_message = email.message_from_bytes(raw_email)
        content = get_email_content(email_message)
        is_html = email_message.get_content_maintype() == "text" and email_message.get_content_subtype() == "html"

        if content:
            subject = decode_header(email_message['Subject'])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            # Pass the is_html flag to indicate if original content is HTML
            save_email(content, subject, num, is_html)
        else:
            print(f'No content: email_{num}')

    # Logout
    mail.logout()

if __name__ == "__main__":
    main()
