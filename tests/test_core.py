import logging
import unittest

from log_record_redactor_py import RecordRedactor


class TestRecordRedactor(unittest.TestCase):
    def _make_record(self, msg, args=None):
        return logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=msg,
            args=args,
            exc_info=None,
        )

    def test_visa_card_with_spaces(self):
        r = self._make_record("card: 4111 1111 1111 1111 done")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "card: ****-****-****-**** done")

    def test_mastercard_with_dashes(self):
        r = self._make_record("payment 5111-2222-3333-4444 ok")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "payment ****-****-****-**** ok")

    def test_amex_15_digits(self):
        r = self._make_record("amex 378282246310005")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "amex ****-****-****-****")

    def test_ssn_dashed(self):
        r = self._make_record("ssn 123-45-6789 here")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "ssn ***-**-**** here")

    def test_no_match_leaves_unchanged(self):
        r = self._make_record("nothing sensitive here")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "nothing sensitive here")

    def test_args_tuple_redacted(self):
        r = self._make_record("card=%s ssn=%s", ("4111 1111 1111 1111", "123-45-6789"))
        RecordRedactor().filter(r)
        self.assertEqual(r.args, ("****-****-****-****", "***-**-****"))

    def test_args_dict_redacted(self):
        r = self._make_record("%(card)s %(ssn)s", {"card": "4111 1111 1111 1111", "ssn": "123-45-6789"})
        RecordRedactor().filter(r)
        self.assertEqual(r.args, {"card": "****-****-****-****", "ssn": "***-**-****"})

    def test_non_string_args_preserved(self):
        r = self._make_record("count=%d", (42,))
        RecordRedactor().filter(r)
        self.assertEqual(r.args, (42,))

    def test_non_string_msg_preserved(self):
        msg_obj = object()
        r = self._make_record(msg_obj)
        RecordRedactor().filter(r)
        self.assertIs(r.msg, msg_obj)

    def test_multiple_matches(self):
        r = self._make_record("c1=4111 1111 1111 1111 c2=5111 2222 3333 4444")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "c1=****-****-****-**** c2=****-****-****-****")

    def test_filter_returns_true(self):
        r = self._make_record("test")
        result = RecordRedactor().filter(r)
        self.assertTrue(result)

    def test_short_numbers_not_redacted(self):
        """Numbers that look like SSNs but are too short should not match."""
        r = self._make_record("id 12345678")
        RecordRedactor().filter(r)
        self.assertEqual(r.msg, "id 12345678")


if __name__ == "__main__":
    unittest.main()
