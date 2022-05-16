from session_save.bot.BotAccountSetting_selnium_login import botAccountSetting
from session_save.setting import botAccount_setting_db

bot_account_setting = botAccountSetting(proxy=True)
client_name = "admin_test"
tmp_count = 1
while botAccount_setting_db.read_account_info_from_db():
    print(f"tmp_count:{tmp_count}")
    bot_account_setting.login(client_name = client_name)
    tmp_count += 1



