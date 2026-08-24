import unittest
import os
import sys

# Append project root directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import uzmovi_dl

class TestVDL(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(uzmovi_dl.sanitize_filename('Test/File:Name*?'), 'TestFileName')
        self.assertEqual(uzmovi_dl.sanitize_filename('../../../etc/passwd'), 'etcpasswd')
        self.assertEqual(uzmovi_dl.sanitize_filename('..'), 'Video')
        self.assertEqual(uzmovi_dl.sanitize_filename('   '), 'Video')

    def test_is_safe_path(self):
        base_dir = os.path.abspath('/tmp/vdl_downloads')
        safe_target = os.path.abspath('/tmp/vdl_downloads/movie/film.mp4')
        unsafe_target = os.path.abspath('/etc/passwd')

        self.assertTrue(uzmovi_dl.is_safe_path(base_dir, safe_target))
        self.assertFalse(uzmovi_dl.is_safe_path(base_dir, unsafe_target))

    def test_check_dependencies(self):
        self.assertTrue(uzmovi_dl.check_dependencies())

    def test_get_video_info_invalid_url(self):
        url, info, err = uzmovi_dl.get_video_info('invalid_scheme://test.com')
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", err)

        url, info, err = uzmovi_dl.get_video_info('ftp://example.com/file')
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan", err)

if __name__ == '__main__':
    unittest.main()
