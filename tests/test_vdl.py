import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uzmovi_dl

class TestVDLCore(unittest.TestCase):

    def test_sanitize_filename(self):
        raw_name = 'Kino: "Xavfli" / Maxfiy * Filmi? <Test> | ../../etc/passwd'
        sanitized = uzmovi_dl.sanitize_filename(raw_name)
        self.assertNotIn(":", sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn("/", sanitized)
        self.assertNotIn("\\", sanitized)
        self.assertNotIn("..", sanitized)
        self.assertEqual(sanitized, "Kino Xavfli  Maxfiy  Filmi Test  etcpasswd")

    def test_is_safe_path(self):
        base_dir = os.path.abspath("/tmp/downloads")
        safe_file = os.path.abspath("/tmp/downloads/uzmovi/movie.mp4")
        unsafe_file = os.path.abspath("/tmp/downloads/../etc/passwd")

        self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_file))
        self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_file))

    def test_check_dependencies(self):
        with patch.dict("sys.modules", {"rich": MagicMock(), "questionary": MagicMock(), "yt_dlp": MagicMock()}):
            self.assertTrue(uzmovi_dl.check_dependencies())

    def test_get_video_info_invalid_url(self):
        url, info, error = uzmovi_dl.get_video_info("invalid_url_without_scheme")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

        url, info, error = uzmovi_dl.get_video_info("file:///etc/passwd")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", error)

    @patch("urllib.request.urlopen")
    def test_get_uzmovi_info_flexible_regex(self, mock_urlopen):
        # Mock HTML responses for Uzmovi main page and iframe page
        main_html = '''
        <html>
        <head><title>Toshkentlik O'g'ri - Uzbek Tilida</title></head>
        <body>
        <iframe src="https://uzdown.xyz/embed/12345?episode=1"></iframe>
        </body>
        </html>
        '''

        iframe_html = '''
        <html>
        <script>
        var player = new Player({
            file: "https://cdn.example.com/hls/movie.m3u8"
        });
        </script>
        </html>
        '''

        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = main_html.encode('utf-8')

        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = iframe_html.encode('utf-8')

        mock_urlopen.side_effect = [mock_resp1, mock_resp2]

        url, info, error = uzmovi_dl.get_uzmovi_info("https://uzmovi.tv/kino/12345")
        self.assertIsNone(error)
        self.assertIsNotNone(info)
        self.assertEqual(info["title"], "Toshkentlik O'g'ri - 1-qism")
        self.assertEqual(info["source_url"], "https://cdn.example.com/hls/movie.m3u8")

if __name__ == "__main__":
    unittest.main()
