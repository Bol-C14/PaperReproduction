"""Known mutations document the byte-screen's deliberately narrow boundary."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED

from screen_rq1_completed import exact_screen, edif_payload


class ExactScreenBoundary(unittest.TestCase):
    def test_identical_copy_passes(self):
        data = b'(instance U (cellRef LUT1) (property INIT (string "2\'h2")))'
        self.assertTrue(exact_screen(data, bytes(bytearray(data))))

    def test_semantic_mutations_rejected_without_interpreting_them(self):
        original = b'(instance U (cellRef LUT1) (property INIT (string "2\'h2")) (portRef I0))'
        mutations = [original.replace(b"h2", b"h1"),
                     original.replace(b"LUT1", b"FDRE"),
                     original.replace(b"I0", b"I1"),
                     original.replace(b' (property INIT (string "2\'h2"))', b"")]
        for data in mutations:
            with self.subTest(data=data):
                self.assertFalse(exact_screen(original, data))

    def test_benign_text_change_is_also_rejected(self):
        self.assertFalse(exact_screen(b"(edif top)", b"(edif  top)"))

    def test_zip_metadata_not_logical_payload(self):
        with TemporaryDirectory() as directory:
            paths = [Path(directory) / "a.dcp", Path(directory) / "b.dcp"]
            for path, compression in zip(paths, [ZIP_STORED, ZIP_DEFLATED]):
                with ZipFile(path, "w", compression=compression) as archive:
                    archive.writestr("top.edf", b"(edif top)")
            self.assertNotEqual(paths[0].read_bytes(), paths[1].read_bytes())
            self.assertTrue(exact_screen(*(edif_payload(path) for path in paths)))


if __name__ == "__main__":
    unittest.main()
