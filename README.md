# Pinginator
The bot is your nightmare. It is your neighbor. It pings all collected users from group.

The main problem is that telegram bot API doesn't provide opportunity to get users from group.
So bot collects them from wrote messages, joined and left user.

## Requirements
```
mongodb
pymongo
PyTelegramBotApi

You have to set environment variables BOT_TOKEN, BOT_LOGIN, BOT_NAME.
```

## Commands

```
/help, /start - print usage

/ping - pings all collected users

Bot configuration: (only by creator)
/quiet_hours - bot won't ping in quiet hours.
/admin_only  - only administrators could use ping functionallity
```

## TO DO:
```
add pagination to /quiet_hours

Group creator usage:
/usage_cost  - you could provide the cost of usage ping functionality. 1 corresponds to 1 hour.
               Please, notice by default user can't hold it more than 3 usages.
/max_usage   - amount of usages that user can collect. Usage cost mode only.
```

## Have fun
