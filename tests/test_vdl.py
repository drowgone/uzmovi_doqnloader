import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uzmovi_dl

class TestVDL(unittest.TestCase):
    def test_check_dependencies(self):
        self.assertTrue(uzmovi_dl.check_dependencies())

    def test_sanitize_filename(self):
        self.assertEqual(uzmovi_dl.sanitize_filename("Film: Title <1>"), "Film Title 1")
        self.assertEqual(uzmovi_dl.sanitize_filename("../../../etc/passwd"), "passwd")
        self.assertEqual(uzmovi_dl.sanitize_filename("..\\..\\..\\etc\\passwd"), "passwd")
        self.assertEqual(uzmovi_dl.sanitize_filename("  "), "Video")

    def test_is_safe_path(self):
        base_dir = os.path.abspath("/tmp/downloads")
        safe_path = os.path.join(base_dir, "movie.mp4")
        unsafe_path = os.path.abspath("/tmp/downloads/../../etc/passwd")

        self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_path))
        self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_path))

    def test_get_video_info_invalid_scheme(self):
        url, info, err = uzmovi_dl.get_video_info("file:///etc/passwd")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", err)

        url, info, err = uzmovi_dl.get_video_info("javascript:alert(1)")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", err)

    @patch('urllib.request.urlopen')
    def test_get_uzmovi_info_regex_flexibility(self, mock_urlopen):
        # Mock HTML response for main page
        main_html = """
        <html>
        <head><title>Avatar 2 - Uzbek Tilida</title></head>
        <body>
        <iframe src="https://uzdown.xyz/embed/12345?episode=1"></iframe>
        </body>
        </html>
        """.encode('utf-8')

        # Mock HTML response for iframe embed
        iframe_html = """
        <html>
        <script>
        var player = new Player({
            file: "https://cdn.example.com/hls/movie.m3u8"
        });
        </script>
        </html>
        """.encode('utf-8')

        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = main_html

        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = iframe_html

        mock_urlopen.side_effect = [mock_resp1, mock_resp2]

        url, info, err = uzmovi_dl.get_uzmovi_info("https://uzmovi.tv/kino/12345")
        self.assertIsNone(err)
        self.assertIsNotNone(info)
        self.assertEqual(info['title'], "Avatar 2 - 1-qism")
        self.assertEqual(info['source_url'], "https://cdn.example.com/hls/movie.m3u8")

if __name__ == '__main__':
    unittest.main()
