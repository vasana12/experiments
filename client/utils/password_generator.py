import string
import random

def generatePassword(passwd=None):
    if passwd is None:
        password_characters = string.ascii_letters + string.digits
        return ''.join(random.choice(password_characters) for i in range(12))
    else:
        return passwd