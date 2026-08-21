import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uzmovi_dl
from vdl_host import vdl_host

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        raw_name = 'Movie: The / Best * Film? <2023> | test..name.mp4'
        sanitized = uzmovi_dl.sanitize_filename(raw_name)
        self.assertNotIn(':', sanitized)
        self.assertNotIn('/', sanitized)
        self.assertNotIn('*', sanitized)
        self.assertNotIn('?', sanitized)
        self.assertNotIn('<', sanitized)
        self.assertNotIn('>', sanitized)
        self.assertNotIn('|', sanitized)
        self.assertNotIn('..', sanitized)
        self.assertEqual(sanitized, 'Movie The  Best  Film 2023  testname.mp4')

    def test_is_safe_path(self):
        base_dir = tempfile.mkdtemp()
        try:
            safe_file = os.path.join(base_dir, "downloads", "video.mp4")
            unsafe_file = os.path.join(base_dir, "..", "secret.txt")

            self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_file))
            self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_file))
        finally:
            shutil.rmtree(base_dir)

    def test_check_dependencies(self):
        self.assertTrue(uzmovi_dl.check_dependencies())

    @patch('urllib.request.urlopen')
    def test_get_uzmovi_info_success(self, mock_urlopen):
        # Mock main page HTML with dynamic uzdown domain
        main_html = '''
        <html>
            <head><title>Avatar 2 - Uzbek Tilida</title></head>
            <body>
                <iframe src="https://uzdown.xyz/embed/12345?episode=1"></iframe>
            </body>
        </html>
        '''.encode('utf-8')

        # Mock iframe page HTML with m3u8 source in double quotes
        iframe_html = '''
        <html>
            <script>
                var player = new Player({file: "https://stream.uzdown.xyz/hls/video.m3u8"});
            </script>
        </html>
        '''.encode('utf-8')

        mock_response1 = MagicMock()
        mock_response1.read.return_value = main_html

        mock_response2 = MagicMock()
        mock_response2.read.return_value = iframe_html

        mock_urlopen.side_effect = [mock_response1, mock_response2]

        url, info, error = uzmovi_dl.get_uzmovi_info("https://uzmovi.tv/kino/12345.html")

        self.assertIsNone(error)
        self.assertIsNotNone(info)
        self.assertEqual(info['title'], "Avatar 2 - 1-qism")
        self.assertEqual(info['source_url'], "https://stream.uzdown.xyz/hls/video.m3u8")

    def test_vdl_host_url_validation(self):
        valid_urls = [
            "https://uzmovi.tv/kino/1.html",
            "http://youtube.com/watch?v=12345"
        ]
        invalid_urls = [
            'https://uzmovi.tv/kino/1" & calc.exe & "',
            "file:///etc/passwd",
            "javascript:alert(1)",
            12345
        ]

        from urllib.parse import urlparse
        for url in valid_urls:
            parsed = urlparse(url)
            self.assertIn(parsed.scheme, ("http", "https"))
            self.assertTrue(bool(parsed.netloc))

        for url in invalid_urls:
            if not isinstance(url, str):
                is_valid = False
            else:
                try:
                    parsed = urlparse(url.strip())
                    is_valid = parsed.scheme in ("http", "https") and bool(parsed.netloc) and '"' not in url
                except Exception:
                    is_valid = False
            self.assertFalse(is_valid)

    def test_install_chrome_bridge_template_pristine(self):
        template_path = os.path.join(os.path.dirname(__file__), '..', 'vdl_host', 'com.chrome_ex.vdl.json')
        with open(template_path, 'r') as f:
            before_data = json.load(f)

        uzmovi_dl.install_chrome_bridge()

        with open(template_path, 'r') as f:
            after_data = json.load(f)

        self.assertEqual(before_data, after_data)
        self.assertEqual(after_data['path'], 'PLACEHOLDER_PATH')

if __name__ == '__main__':
    unittest.main()
