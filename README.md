# Pinginator
The bot is your nightmare. It is your neighbor. It pings all collected users from the group.

The main problem is that telegram bot API doesn't provide an opportunity to get users from the group.
So bot collects them from wrote messages, joined and left user.

Feel free to test the bot: <https://www.t.me/pinginatorbot>

## Requirements
```
pymongo
python-telegram-bot

You have to set environment variables BOT_TOKEN, BOT_LOGIN, BOT_NAME, DB in bot.env

BOT_TOKEN - to provide telegram bot token
DB - to provide the name of the database that should be used by the bot. Please, note that bot will use the `groups` collection.
MONGODB_URI - to provide a mongodb server
```


# Execution
```
Edit bot.env variables
docker-compose up -d
You are great
```


## Commands

```
/help, /start - print usage

/ping - pings all collected users

Bot configuration: (only for the creator of group)
/quiet_hours - bot won't ping in quiet hours.
/admin_only  - only administrators could use ping functionality
```

## TODO:
Project board: <https://github.com/akorchyn/Pinginator/projects/1>

## Have fun
