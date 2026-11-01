import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pii_guard import detect, luhn_valid, redact, residual_risks, valid_sa_id  # noqa: E402


class ChecksumTests(unittest.TestCase):
    def test_luhn(self):
        self.assertTrue(luhn_valid("79927398713"))   # standard textbook Luhn example
        self.assertFalse(luhn_valid("79927398710"))

    def test_sa_id_needs_valid_date(self):
        # Same digits but month 13: must be rejected even if the checksum were fine.
        self.assertFalse(valid_sa_id("8513015800084"))


class DetectionTests(unittest.TestCase):
    def kinds(self, text):
        return [kind for kind, *_ in detect(text)]

    def test_phone_formats(self):
        for text in ["082 555 1234", "0825551234", "+27 82 555 1234", "082-555-1234"]:
            self.assertEqual(self.kinds(f"call {text} now"), ["PHONE"], text)

    def test_email(self):
        self.assertEqual(self.kinds("mail thabo.12@example.com today"), ["EMAIL"])

    def test_invoice_number_is_not_an_id(self):
        self.assertEqual(self.kinds("Invoice 1234567890123 overdue"), [])

    def test_lowercase_word_is_not_a_name(self):
        self.assertEqual(self.kinds("a 30-day grace period"), [])


class RedactionTests(unittest.TestCase):
    def test_redact_replaces_with_placeholders(self):
        clean, findings = redact("Lerato: lerato@example.org, 082 555 1234")
        self.assertEqual(clean, "[NAME]: [EMAIL], [PHONE]")
        self.assertEqual(len(findings), 3)

    def test_residual_scan_flags_long_digit_runs(self):
        self.assertEqual(residual_risks("Ref 1234567890123 kept"), ["1234567890123"])
        self.assertEqual(residual_risks("[NAME] says hi"), [])


if __name__ == "__main__":
    unittest.main()
