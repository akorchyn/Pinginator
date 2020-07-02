# Pinginator
The bot is your nightmare. It is your neighbor. It pings all collected users from the group.

The main problem is that telegram bot API doesn't provide an opportunity to get users from the group.
So bot collects them from wrote messages, joined and left user.

Feel free to test the bot: <https://www.t.me/pinginatorbot>

## Requirements
```
mongodb
pymongo
PyTelegramBotApi

You have to set environment variables BOT_TOKEN, BOT_LOGIN, BOT_NAME, MONGODB_URI, DB.

BOT_TOKEN - to provide telegram bot token
BOT_LOGIN - to provide a bot tag (for example @pinginatorbot)
BOT_NAME - to provide the name of the bot (for example Pinginator)
MONGODB_URI - to provide the credentials to the MongoDB connection (for example localhost)
DB - to provide the name of the database that should be used by the bot. Please, note that bot will use the `groups` collection.
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
Project board: <https://github.com/users/akorchyn/projects/1>

## Have fun
