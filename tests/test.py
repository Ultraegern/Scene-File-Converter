import os
import tempfile
import unittest

from main import M32, MixerScene


class TestMixerScene(unittest.TestCase):
    def test_decode_full_sample(self):
        scene = M32.decode('m32ExsampleFull.scn')
        self.assertIsInstance(scene, MixerScene)
        self.assertEqual(scene.name, 'm32ExsampleFull')
        self.assertEqual(len(scene.input_channels.channels), 32)

    def test_json_roundtrip(self):
        scene = M32.decode('m32ExsampleFull.scn')
        # save to a temporary file
        fd, path = tempfile.mkstemp(prefix='scene_', suffix='.json', dir='.')
        os.close(fd)
        try:
            scene.save_json(path)
            loaded = MixerScene.load_json(path)
            self.assertEqual(loaded.name, scene.name)
            # check a couple of fields on channel 2 (index 1)
            orig = scene.input_channels.channels[1]
            new = loaded.input_channels.channels[1]
            self.assertEqual(orig.name, new.name)
            self.assertAlmostEqual(orig.gain, new.gain)
            self.assertEqual(orig.equalizer_enabled, new.equalizer_enabled)
            # eq bands should be 4
            self.assertEqual(len(new.equalizer.bands), 4)
        finally:
            try:
                os.remove(path)
            except Exception:
                pass


if __name__ == '__main__':
    unittest.main()
