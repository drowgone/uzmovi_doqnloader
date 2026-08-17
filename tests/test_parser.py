import unittest
from parser import sanitize_filename, is_safe_path, get_video_info

class TestParser(unittest.TestCase):
    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("movie:name?.mp4"), "moviename.mp4")
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("   "), "Video")

    def test_is_safe_path(self):
        base = "/tmp/downloads"
        safe_target = "/tmp/downloads/movie/film.mp4"
        unsafe_target = "/tmp/downloads/../../etc/passwd"

        self.assertTrue(is_safe_path(base, safe_target))
        self.assertFalse(is_safe_path(base, unsafe_target))

    def test_get_video_info_invalid_url(self):
        url, info, err = get_video_info("invalid_url_scheme")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan yoki noto'g'ri URL!", err)

        url, info, err = get_video_info("ftp://example.com/video")
        self.assertIsNone(info)
        self.assertIn("Xavfsiz bo'lmagan yoki noto'g'ri URL!", err)

if __name__ == "__main__":
    unittest.main()
