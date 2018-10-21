import re


def my_rstrip(string):
    if string:
        while re.match('^[\w-]', string[-1]) is None:
            if string[-1] == '.' \
                    or string[-1] == ')'\
                    or string[-1] == '?'\
                    or string[-1] == '!':
                break
            string = string[:-1]
            if len(string) == 0:
                break
        return string
    else:
        return None


def is_not_empty(string):
    if string is not None and len(re.findall(r'(\S+)', string)) > 0:
        return True
    else:
        return False
