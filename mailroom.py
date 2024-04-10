import json

from src.account import process_account

DIR_BACKUP = 'backup'


def main() -> None:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    for account in config['accounts']:
        process_account(account, DIR_BACKUP)


if __name__ == "__main__":
    main()
