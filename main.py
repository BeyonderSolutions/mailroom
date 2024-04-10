import email
import imaplib
import os
from email.header import decode_header
from typing import Union
from rich import print

from secret import account_email, account_password, host
from src.utils import status

DIR_BACKUP = 'backup'

# Function to get the HTML part of the email
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

# Create a directory for emails if it doesn't exist
email_dir = DIR_BACKUP
if not os.path.exists(email_dir):
    os.makedirs(email_dir)

# Login to IMAP server
imap_host = host
user = account_email  # Your email
password = account_password  # Your email account password

mail = imaplib.IMAP4_SSL(imap_host)
mail.login(user, password)
mail.select('inbox')  # Select the mailbox you want to back up

# Search for all emails in the inbox
status, messages = mail.search(None, 'ALL')
messages = messages[0].split(b' ')

for num, mail_id in enumerate(messages, 1):
    # Fetch each email (RFC822 protocol for fetching full email)
    status, data = mail.fetch(mail_id, '(RFC822)')
    raw_email = data[0][1]

    # Parse the raw email using email library
    email_message = email.message_from_bytes(raw_email)
    html_part = get_html_part(email_message)

    if html_part:
        # Decode email subject for filename (optional)
        subject = decode_header(email_message['Subject'])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        # Replace any filesystem-unsafe characters in the subject
        filename_safe_subject = "".join(i for i in subject if i not in "\/:*?<>|")
        filename = os.path.join(email_dir, f"email_{num}_{filename_safe_subject}.html")

        # Save the HTML part to a file
        with open(filename, 'wb') as f:
            f.write(html_part)

        print(f'Saved: {filename}')
    else:
        print(f'No HTML content: email_{num}')

# Logout
mail.logout()