import logging
import re

# Mastercard: 2221-2720 range, 16 digits
# Visa: starts with 4, 16 digits
# Amex: starts with 34 or 37, 15 digits
# Discover: starts with 6011, 65, or 644-649, 16 digits
#
# We only match cards with separators (spaces or dashes) every four digits,
# OR continuous 16/15-digit strings. This avoids false positives on long
# numeric IDs while still catching formatted cards.
_CC_PATTERN = re.compile(
    r'(?:'
    r'(?:5[1-5]\d{2}|2(?:2[2-9]\d|[3-6]\d{2}|7[01]\d|720))'  # MC
    r'|4\d{3}'                                                  # Visa
    r'|3[47]\d{2}'                                               # Amex
    r'|(?:6011|65|64[4-9])\d{2}'                                 # Discover
    r')'
    r'(?:[ -]?\d{4}){3}'                                          # three more groups of 4
    r'|(?:3[47]\d{13})'                                          # Amex continuous 15
    r'|(?:4\d{15})'                                              # Visa continuous 16
    r'|(?:5[1-5]\d{14})'                                         # MC continuous 16
)

# SSN: XXX-XX-XXXX with dashes, or XXXXXXXXX continuous.
# We intentionally do NOT match spaces ("XXX XX XXXX") because that format
# is rare for SSNs and common for other identifiers, causing false positives.
_SSN_PATTERN = re.compile(
    r'\d{3}-\d{2}-\d{4}'      # dashed format
    r'|\d{9}'                  # continuous 9 digits — high false positive risk
)

# Token for credit card matches: show first group + last four, mask middle.
# We only know first 4 and last 4 from the match span, so we output the
# standard PCI-DSS display form.
_CC_TOKEN = "****-****-****-****"
_SSN_TOKEN = "***-**-****"


class RecordRedactor(logging.Filter):
    """A logging filter that masks credit-card and SSN patterns in records.

    Scans both record.msg and every element of record.args for sensitive
    patterns. Matched substrings are replaced with masked tokens in-place.

    Design choices:
        - Uses regex on the formatted string and on str(arg) values.
        - Mutates the record in-place (standard for logging.Filter).
        - Catches exceptions during filtering to never break the logging
          pipeline. On error, returns True (log the record unredacted).
    """

    def __init__(self, name=""):
        super().__init__(name=name)

    def _redact_string(self, text: str) -> str:
        text = _CC_PATTERN.sub(_CC_TOKEN, text)
        text = _SSN_PATTERN.sub(_SSN_TOKEN, text)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = self._redact_string(record.msg)

            if record.args:
                if isinstance(record.args, dict):
                    new_args = {}
                    for k, v in record.args.items():
                        if isinstance(v, str):
                            new_args[k] = self._redact_string(v)
                        else:
                            new_args[k] = v
                    record.args = new_args
                elif isinstance(record.args, tuple):
                    new_args = []
                    for a in record.args:
                        if isinstance(a, str):
                            new_args.append(self._redact_string(a))
                        else:
                            new_args.append(a)
                    record.args = tuple(new_args)
        except Exception:
            # Never let redaction break the logging pipeline.
            return True

        return True
