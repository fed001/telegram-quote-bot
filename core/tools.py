import re


def is_not_empty(string):
    if string is not None and len(re.findall(r'(\S+)', string)) > 0:
        return True
    else:
        return False
