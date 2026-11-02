import unittest
from rq4_timestamp_v1 import canonicalize_timestamp_v1 as canonical

FIXTURE = b'''(edif top
(status
  (written
  (timeStamp 2026 11 02 11 29 52)
  (program "Vivado")))
(library primitives
(cell LUT1 (instance U (cellRef LUT1) (property INIT (string "2'h2")) (portRef I0))))
'''


class TimestampOnlyScreen(unittest.TestCase):
    def test_same_and_timestamp_only(self):
        self.assertEqual(canonical(FIXTURE), canonical(bytes(bytearray(FIXTURE))))
        self.assertEqual(canonical(FIXTURE), canonical(FIXTURE.replace(b"11 29 52", b"11 33 46")))

    def test_semantic_or_other_text_changes_remain(self):
        for old, new in [(b"h2", b"h1"), (b"LUT1)", b"FDRE)"),
                         (b"I0", b"I1"), (b'"Vivado"', b'"other"'),
                         (b"(library ", b"(library  ")]:
            with self.subTest(old=old):
                self.assertNotEqual(canonical(FIXTURE), canonical(FIXTURE.replace(old, new)))

    def test_unknown_and_duplicate_headers_rejected(self):
        for text in [FIXTURE.replace(b"timeStamp", b"timestamp"), FIXTURE+FIXTURE,
                     FIXTURE.replace(b"(edif ", b"(unknown ")]:
            with self.subTest(text=text[:20]):
                with self.assertRaises(ValueError):
                    canonical(text)

    def test_timestamp_named_property_preserved(self):
        other = FIXTURE.replace(b"(cell LUT1", b'(property timeStamp (string "changed")) (cell LUT1')
        self.assertNotEqual(canonical(FIXTURE), canonical(other))


if __name__ == "__main__":
    unittest.main()
