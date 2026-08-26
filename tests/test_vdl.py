import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add root directory to sys.path so we can import uzmovi_dl
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uzmovi_dl

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(uzmovi_dl.sanitize_filename("Test / Movie * 123?"), "Test  Movie  123")
        self.assertEqual(uzmovi_dl.sanitize_filename("../../../etc/passwd"), "etcpasswd")
        self.assertEqual(uzmovi_dl.sanitize_filename("..\\..\\Windows\\System32"), "WindowsSystem32")
        self.assertEqual(uzmovi_dl.sanitize_filename(""), "Video")

    def test_is_safe_path(self):
        base_dir = os.path.abspath("/tmp/downloads")
        safe_path = os.path.abspath("/tmp/downloads/uzmovi/movie.mp4")
        unsafe_path = os.path.abspath("/tmp/downloads/../etc/passwd")

        self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_path))
        self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_path))

    def test_check_dependencies(self):
        self.assertTrue(uzmovi_dl.check_dependencies())

    def test_get_video_info_invalid_url(self):
        url, info, error = uzmovi_dl.get_video_info("ftp://invalid-url.com/file.mp4")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan yoki noto'g'ri URL", error)

        url, info, error = uzmovi_dl.get_video_info("invalid_url_without_scheme")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan yoki noto'g'ri URL", error)

    @patch("urllib.request.urlopen")
    def test_get_uzmovi_info_regex_matching(self, mock_urlopen):
        # Mocking main html response and iframe html response
        main_html = """
        <html>
            <head><title>Avatar 2 - Uzbek Tilida</title></head>
            <body>
                <iframe src="https://uzdown.xyz/embed/12345?episode=1"></iframe>
            </body>
        </html>
        """.encode('utf-8')

        iframe_html = """
        <html>
            <script>
                var player = new Player({
                    file: 'https://cdn.uzdown.xyz/hls/stream.m3u8'
                });
            </script>
        </html>
        """.encode('utf-8')

        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = main_html
        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = iframe_html

        mock_urlopen.side_effect = [mock_resp1, mock_resp2]

        url, info, error = uzmovi_dl.get_uzmovi_info("https://uzmovi.tv/kino/12345.html")
        self.assertIsNone(error)
        self.assertIsNotNone(info)
        self.assertEqual(info['title'], "Avatar 2 - 1-qism")
        self.assertEqual(info['source_url'], "https://cdn.uzdown.xyz/hls/stream.m3u8")

if __name__ == '__main__':
    unittest.main()
