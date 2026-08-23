import unittest
import os
import sys
import re

# Add repo root directory to python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import uzmovi_dl

class TestVDL(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(uzmovi_dl.sanitize_filename("Avatar: The Way of Water"), "Avatar The Way of Water")
        self.assertEqual(uzmovi_dl.sanitize_filename("../../../etc/passwd"), "passwd")
        self.assertEqual(uzmovi_dl.sanitize_filename("Film?Name*<1>"), "FilmName1")
        self.assertEqual(uzmovi_dl.sanitize_filename(""), "Video")

    def test_is_safe_path(self):
        base_dir = os.path.abspath("/tmp/downloads")
        safe_path = os.path.join(base_dir, "uzmovi", "Movie.mp4")
        unsafe_path = os.path.abspath("/tmp/downloads/../../etc/passwd")

        self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_path))
        self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_path))

    def test_get_video_info_invalid_url(self):
        _, info, error = uzmovi_dl.get_video_info("invalid_url_without_scheme")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

        _, info, error = uzmovi_dl.get_video_info("javascript:alert(1)")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

    def test_uzdown_regex_matching(self):
        pattern = r'src=["\']?(https://[a-zA-Z0-9.-]*uzdown[a-zA-Z0-9.-]*/embed/[^"\'\s>]+)'

        urls = [
            'src="https://uzdown.live/embed/12345"',
            'src="https://uzdown.tv/embed/67890"',
            "src='https://uzdown.xyz/embed/test'",
            'src="https://server1.uzdown.cc/embed/play"'
        ]

        for text in urls:
            match = re.search(pattern, text)
            self.assertIsNotNone(match, f"Failed to match: {text}")

    test_m3u8_regex_matching = None

    def test_m3u8_regex_matching(self):
        html1 = "file: 'https://cdn.example.com/stream/index.m3u8'"
        html2 = 'file: "https://cdn.example.com/stream/index.m3u8"'
        html3 = '<source src="https://cdn.example.com/stream/index.m3u8" type="application/x-mpegURL">'

        m1 = re.search(r"file:\s*['\"]([^'\"]+)['\"]", html1) or \
             re.search(r'src=["\']([^"\']+\.m3u8[^"\']*)["\']', html1)
        self.assertIsNotNone(m1)
        self.assertEqual(m1.group(1), "https://cdn.example.com/stream/index.m3u8")

        m2 = re.search(r"file:\s*['\"]([^'\"]+)['\"]", html2) or \
             re.search(r'src=["\']([^"\']+\.m3u8[^"\']*)["\']', html2)
        self.assertIsNotNone(m2)
        self.assertEqual(m2.group(1), "https://cdn.example.com/stream/index.m3u8")

        m3 = re.search(r"file:\s*['\"]([^'\"]+)['\"]", html3) or \
             re.search(r'src=["\']([^"\']+\.m3u8[^"\']*)["\']', html3)
        self.assertIsNotNone(m3)
        self.assertEqual(m3.group(1), "https://cdn.example.com/stream/index.m3u8")

if __name__ == '__main__':
    unittest.main()
