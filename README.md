# Pinginator
The bot is your nightmare. It is your neighbor. It pings all collected users from the group.

The main problem is that telegram bot API doesn't provide an opportunity to get users from the group.
So bot collects them from messages, telegram status updates(joined users, etc)

Feel free to test the bot: <https://www.t.me/pinginatorbot>

## Requirements
```
pymongo
python-telegram-bot

You have to set environment variables BOT_TOKEN, MONGODB_URI

BOT_TOKEN - to provide telegram bot token
DB_URL - to provide a MongoDB server

Optional:
DB - to provide the name of the database that should be used by the bot. Please, note that bot will use the `groups` collection.
     PinginatorDb is used by default
OWNER_ID - to provide a telegram user to which bot will send unhandled exceptions. (I hope, it won't)
           Please, note that the user should activate chat with the bot first.
```


## Execution
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
/schedule - to schedule a new respiting message
/unschedule - to unschedule a scheduled message
```

## TODO:
Project board: <https://github.com/akorchyn/Pinginator/projects/1>

## Have fun
