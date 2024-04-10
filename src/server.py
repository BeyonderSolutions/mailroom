import imaplib


def connect_to_server(imap_host, user, password) -> imaplib.IMAP4_SSL:
    mail = imaplib.IMAP4_SSL(imap_host)
    mail.login(user, password)
    return mail