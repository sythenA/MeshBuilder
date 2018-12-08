
encoding = ['utf-8',
            'big5']


def toUnicode(string):
    for coding in encoding:
        try:
            string = unicode(string.decode(coding))
            return string
        except(UnicodeDecodeError, UnicodeEncodeError):
            continue

    return string
