import unittest
import os
import sys
import tempfile
import urllib.parse

from uzmovi_dl import sanitize_filename, is_safe_path, get_video_info, get_uzmovi_info

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("Title: Subtitle / Part 1"), "Title Subtitle  Part 1")
        self.assertEqual(sanitize_filename("../../etc/passwd"), "etcpasswd")
        self.assertEqual(sanitize_filename("valid_name.mp4"), "valid_name.mp4")
        self.assertEqual(sanitize_filename('File?*"<>|Name'), "FileName")
        self.assertEqual(sanitize_filename(""), "Video")

    def test_is_safe_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            safe_file = os.path.join(tmpdir, "video.mp4")
            self.assertTrue(is_safe_path(tmpdir, safe_file))

            unsafe_file = os.path.join(tmpdir, "..", "secret.txt")
            self.assertFalse(is_safe_path(tmpdir, unsafe_file))

    def test_get_video_info_invalid_url(self):
        url, info, error = get_video_info("invalid_url_without_scheme")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

        url, info, error = get_video_info("ftp://example.com/video.mp4")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

if __name__ == '__main__':
    unittest.main()
