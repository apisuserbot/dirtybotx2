from emilia.sample_config import Config


class Development(Config):
    OWNER_ID = 1411273575  # my telegram ID
    OWNER_USERNAME = "X_Imfine"  # my telegram username
    API_KEY = "1463504029:AAF9ojbdMw6ke4MtyNNmgamUOqrGjDemz9o"  # my api key, as provided by the botfather
    MESSAGE_DUMP = '-1001465500706' # some group chat that your bot is a member of
    USE_MESSAGE_DUMP = True
    SUDO_USERS = [1411273575]  # List of id's for users which have sudo access to the bot.
    SUPPORT_USERS = [1411273575]  # List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    WHITELIST_USERS = []  # List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    LOAD = []
    NO_LOAD = ['translation']
