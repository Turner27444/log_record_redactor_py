# log_record_redactor_py

A `logging.Filter` that scans log records for credit-card and Social Security number patterns and replaces them with masked tokens.

```python
import logging
from log_record_redactor_py import RecordRedactor

logger = logging.getLogger("myapp")
logger.addFilter(RecordRedactor())

logger.info("card=%s", "4111 1111 1111 1111")
# Record stored with msg="card=%s", args=("****-****-****-****",)
```

## Why

Log pipelines frequently pass through messages containing identifiers that must not reach downstream sinks in clear text. Doing full structured redaction at emit time — without depending on a third-party logging framework — means wrapping the standard `logging.Filter` interface and rewriting `record.msg` and `record.args` before handlers see them.

The trade-off: regex-based pattern matching is fast and dependency-free, but it produces false positives and false negatives. A 16-digit order number will be redacted as if it were a Visa card. A Social Security number written with spaces (`123 45 6789`) will not be caught. This library accepts that trade-off for the sake of zero dependencies and a small, auditable surface.

## Edge cases

- `record.args` can be a tuple or a dict; both are handled. Non-string args are passed through untouched.
- If `record.msg` is not a string (some libraries pass objects), it is left as-is.
- The filter catches its own exceptions and always returns `True`, so a redaction error never breaks the logging pipeline.
