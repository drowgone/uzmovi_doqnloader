import unittest
import os
import shutil
from downloader import check_ffmpeg
from uzmovi_dl import check_dependencies, get_config_dir

class TestUzmoviDL(unittest.TestCase):
    def test_check_dependencies(self):
        self.assertTrue(check_dependencies())

    def test_check_ffmpeg(self):
        result = check_ffmpeg()
        self.assertEqual(result, shutil.which("ffmpeg") is not None)

    def test_get_config_dir(self):
        config_dir = get_config_dir()
        self.assertTrue(config_dir.endswith("uzmovi"))

if __name__ == "__main__":
    unittest.main()
