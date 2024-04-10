# 📮 mailroom
Bulk email account backup tool.

## Usage
Create a `config.json` file in the same directory as the script with the following content:
```json
{
    "accounts": [
        {
            "host": "mail.mailserver.com",
            "email": "user1@email.com",
            "password": "password"
        },
        {
            "host": "mail.mailserver.com",
            "email": "user2@email.com",
            "password": "password"
        }
    ]
}
```

Run the script.
```bash
python mailroom.py
```
