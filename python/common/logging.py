import logging
import re

SECRET_RE = re.compile(r'(password|token|authorization|secret|api_v3_key)(["\s:=]+)([^\s,"}]+)', re.I)


def redact(text):
    return SECRET_RE.sub(r'\1\2***', str(text))


class RedactFilter(logging.Filter):
    def filter(self, record):
        record.msg = redact(record.getMessage())
        record.args = ()
        return True
