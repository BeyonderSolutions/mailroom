import email
import imaplib
import os

from .email import save_email
from .server import connect_to_server


def process_account(account: dict, backup_root_dir: str) -> None:
    host = account['host']
    user_email = account['email']
    user_password = account['password']

    backup_dir = os.path.join(backup_root_dir, user_email)
    os.makedirs(backup_dir, exist_ok=True)

    mail = connect_to_server(host, user_email, user_password)
    messages = search_emails(mail)
    if not messages:
        print(f"No messages to fetch for {user_email}")
        return

    for num, mail_id in enumerate(messages, 1):
        try:
            status, data = mail.fetch(mail_id, '(BODY.PEEK[])')
            if status != 'OK':
                print(f"Failed to fetch email with ID {mail_id.decode()}")
                continue
            email_message = email.message_from_bytes(data[0][1])
            save_email(email_message, num, backup_dir)
        except imaplib.IMAP4.error as e:
            print(f"An error occurred while fetching email with ID {mail_id.decode()}: {e}")

    mail.logout()
    print(f'Finished backup for account: {user_email}')


def search_emails(mail) -> list:
    mail.select('inbox')
    status, messages = mail.search(None, 'ALL')
    if status != 'OK':
        print("No messages found!")
        return []
    message_list = messages[0].split(b' ')
    if message_list == [b'']:
        return []
    return message_list