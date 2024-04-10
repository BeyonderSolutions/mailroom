import datetime
import email
import os
from email.header import decode_header
from email.message import Message
from typing import Tuple, Union


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

def parse_email_date(email_message: Message) -> str:
    date_tuple = email.utils.parsedate_tz(email_message['Date'])
    if date_tuple:
        local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        return local_date.strftime('%Y-%m-%d %H:%M')
    return 'unknown_date'

def get_sender_email(email_message: Message) -> str:
    sender = email_message.get('From', 'unknown_sender')
    return email.utils.parseaddr(sender)[1]

def decode_subject(subject: Tuple[bytes, str]) -> str:
    decoded_subject = decode_header(subject)[0][0]
    if isinstance(decoded_subject, bytes):
        decoded_subject = decoded_subject.decode(errors='ignore')
    return "".join(i for i in decoded_subject if i not in "\/:*?<>|")

def create_email_dir(base_dir: str, date: str, sender_email: str, subject: str) -> str:
    email_dir_name = f"{date} - {sender_email} - {subject}"
    email_dir = os.path.join(base_dir, email_dir_name)
    os.makedirs(email_dir, exist_ok=True)
    return email_dir

def save_attachments_and_body(email_message: Message, email_dir: str) -> None:
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
    
def save_email(email_message: Message, email_num: int, backup_dir: str) -> None:
    formatted_date = parse_email_date(email_message)
    sender_email = get_sender_email(email_message)
    subject = decode_subject(email_message['Subject'])
    email_dir = create_email_dir(backup_dir, formatted_date, sender_email, subject)
    save_attachments_and_body(email_message, email_dir)
    print(f'Saved email and attachments to: {email_dir}')