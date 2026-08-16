import unittest
import os
import sys
import tempfile
from parser import (
    sanitize_filename,
    is_safe_path,
    get_video_info
)
from uzmovi_dl import check_dependencies

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Kino: Test?"), "Kino Test")
        self.assertEqual(sanitize_filename("../../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("   "), "Video")

    def test_is_safe_path(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            safe_target = os.path.join(tmp_dir, "downloads", "video.mp4")
            self.assertTrue(is_safe_path(tmp_dir, safe_target))

            unsafe_target = os.path.realpath(os.path.join(tmp_dir, "..", "outside.mp4"))
            self.assertFalse(is_safe_path(tmp_dir, unsafe_target))

    def test_check_dependencies(self):
        self.assertTrue(check_dependencies())

    def test_get_video_info_invalid_scheme(self):
        url, info, error = get_video_info("ftp://example.com/video")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

    def test_get_video_info_command_injection_attempt(self):
        url, info, error = get_video_info("https://uzmovi.tv/kino/1\" & calc.exe & \"")
        self.assertTrue(url.startswith("https://"))

if __name__ == '__main__':
    unittest.main()
