import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Import modules to test
import uzmovi_dl

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(uzmovi_dl.sanitize_filename("test/file:name?*"), "testfilename")
        self.assertEqual(uzmovi_dl.sanitize_filename("../../etc/passwd"), "etcpasswd")
        self.assertEqual(uzmovi_dl.sanitize_filename("..\\..\\Windows\\System32"), "WindowsSystem32")
        self.assertEqual(uzmovi_dl.sanitize_filename("  Movie Title 123  "), "Movie Title 123")
        self.assertEqual(uzmovi_dl.sanitize_filename("???"), "Video")

    def test_is_safe_path(self):
        base = "/home/user/downloads"
        if os.name == 'nt':
            base = "C:\\Users\\User\\Downloads"
            safe_target = "C:\\Users\\User\\Downloads\\movie.mp4"
            unsafe_target = "C:\\Windows\\System32\\calc.exe"
        else:
            safe_target = "/home/user/downloads/uzmovi/movie.mp4"
            unsafe_target = "/etc/passwd"

        self.assertTrue(uzmovi_dl.is_safe_path(base, safe_target))
        self.assertFalse(uzmovi_dl.is_safe_path(base, unsafe_target))

    def test_url_validation_get_video_info(self):
        # Invalid URLs
        bad_urls = [
            "javascript:alert(1)",
            "file:///etc/passwd",
            "ftp://example.com/file",
            "invalid_url_without_scheme",
            "http://"
        ]
        for url in bad_urls:
            orig, info, err = uzmovi_dl.get_video_info(url)
            self.assertIsNone(info)
            self.assertIsNotNone(err)

    def test_check_dependencies(self):
        self.assertTrue(uzmovi_dl.check_dependencies())

    @patch('urllib.request.urlopen')
    def test_get_uzmovi_info_success(self, mock_urlopen):
        html_page = """
        <html>
        <head><title>Avatar 2 - Uzmovi.tv</title></head>
        <body>
        <iframe src="https://uzdown.xyz/embed/12345?episode=1"></iframe>
        </body>
        </html>
        """
        iframe_page = """
        <html>
        <script>
        var player = new Player({file: 'https://cdn.uzdown.xyz/hls/stream.m3u8'});
        </script>
        </html>
        """

        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = html_page.encode('utf-8')

        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = iframe_page.encode('utf-8')

        mock_urlopen.side_effect = [mock_resp1, mock_resp2]

        url = "https://uzmovi.tv/kino/123-avatar-2.html"
        orig, info, err = uzmovi_dl.get_uzmovi_info(url)

        self.assertIsNone(err)
        self.assertIsNotNone(info)
        self.assertEqual(info['title'], "Avatar 2 - 1-qism")
        self.assertEqual(info['source_url'], "https://cdn.uzdown.xyz/hls/stream.m3u8")

if __name__ == '__main__':
    unittest.main()
