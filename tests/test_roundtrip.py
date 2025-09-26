import os
import tempfile
import unittest

from main import M32, MixerScene


class TestRoundtrip(unittest.TestCase):
    def assert_structs_almost_equal(self, a, b, tol=1e-3):
        """Recursively compare two structures (dict/list/primitive), allowing
        small numeric differences.
        """
        if isinstance(a, dict) and isinstance(b, dict):
            self.assertEqual(set(a.keys()), set(b.keys()), msg=f"Dict keys differ: {set(a.keys())} vs {set(b.keys())}")
            for k in a.keys():
                self.assert_structs_almost_equal(a[k], b[k], tol=tol)
            return
        if isinstance(a, list) and isinstance(b, list):
            self.assertEqual(len(a), len(b), msg=f"List lengths differ: {len(a)} vs {len(b)}")
            for x, y in zip(a, b):
                self.assert_structs_almost_equal(x, y, tol=tol)
            return
        # numbers: allow tolerance
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            # treat NaN/inf as exact equality via str comparison
            try:
                self.assertAlmostEqual(float(a), float(b), delta=tol)
            except AssertionError:
                # produce a clearer message
                self.fail(f"Numeric values differ: {a} vs {b}")
            return
        # fallback exact equality for bools/strings/etc.
        self.assertEqual(a, b, msg=f"Values differ: {a!r} vs {b!r}")

    def test_scn_json_roundtrip(self):
        # decode original .scn
        original = M32.decode('m32ExsampleFull.scn')

        # save to temporary json
        fd_json, path_json = tempfile.mkstemp(prefix='scene_rt_', suffix='.json', dir='.')
        os.close(fd_json)

        # will write the regenerated .scn here
        fd_scn, path_scn = tempfile.mkstemp(prefix='scene_rt_', suffix='.scn', dir='.')
        os.close(fd_scn)

        try:
            original.save_json(path_json)

            # load the JSON and write back to .scn
            loaded_from_json = MixerScene.load_json(path_json)
            loaded_from_json.save_m32(path_scn)

            # import the saved JSON and the saved SCN and compare
            json_scene = MixerScene.load_json(path_json)
            scn_scene = M32.decode(path_scn)

            # compare their dict representations allowing tiny float diffs
            self.assert_structs_almost_equal(json_scene.to_dict(), scn_scene.to_dict())
        finally:
            for p in (path_json, path_scn):
                try:
                    os.remove(p)
                except Exception:
                    pass


if __name__ == '__main__':
    unittest.main()
