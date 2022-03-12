from session_save.bot.BotAccountSetting_update_1 import botAccountSetting
from session_save.setting import botAccount_setting_db

bot_account_setting = botAccountSetting()

while botAccount_setting_db.read_account_info_from_db():
    bot_account_setting.login()


