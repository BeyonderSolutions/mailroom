import email
import imaplib
import os
from email.header import decode_header

from rich import print
from rich.console import Console

from secret import account_email, account_password, host

DIR_BACKUP = 'emails_backup'

# Create a directory for emails if it doesn't exist
email_dir = os.path.join(DIR_BACKUP)
if not os.path.exists(email_dir):
    os.makedirs(email_dir)

# Login to IMAP server
imap_host = host
user = account_email
password = account_password

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
    
    # Decode email subject for filename (optional)
    subject = decode_header(email_message['Subject'])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode()
    # Replace any filesystem-unsafe characters in the subject
    filename_safe_subject = "".join(i for i in subject if i not in "\/:*?<>|")
    filename = os.path.join(email_dir, f"email_{num}_{filename_safe_subject}.eml")
    
    # Save the email to a file
    with open(filename, 'wb') as f:
        f.write(raw_email)

    print(f'Saved: {filename}')

# Logout
mail.logout()
