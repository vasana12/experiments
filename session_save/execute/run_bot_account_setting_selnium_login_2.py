from session_save.bot.BotAccountSetting_selnium_login import botAccountSetting
from session_save.setting import botAccount_setting_db


bot_account_setting = botAccountSetting(proxy=True)
client_name = "admin_test"
while botAccount_setting_db.read_account_info_from_db():
    bot_account_setting.login(client_name = client_name)



