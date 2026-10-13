"""Regression checks for stale Python/JAR rejection at the APK build boundary."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('core_inputs',ROOT/'scripts/check_core_runtime_inputs.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def sha(data):return hashlib.sha256(data).hexdigest()
class RuntimePackaging(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.assets=self.root/'app/src/main/assets/core';self.assets.mkdir(parents=True)
        script=b'print("old")\n';(self.assets/'mobile_core.py').write_bytes(script)
        with zipfile.ZipFile(self.assets/'python-home.zip','w') as z:z.writestr('scripts/mobile_core.py',script)
        jar=self.root/'app/libs/Qt6Android.jar';jar.parent.mkdir(parents=True);jar.write_bytes(b'fixture-jar')
        lib=self.root/'app/src/main/jniLibs/arm64-v8a/libFixture.so';lib.parent.mkdir(parents=True);lib.write_bytes(b'fixture-library')
        manifest={'asset_zip_sha256':sha((self.assets/'python-home.zip').read_bytes()),'java_jar_sha256':sha(jar.read_bytes()),'libraries':{lib.name:sha(lib.read_bytes())},'python_assets':[{'path':'scripts/mobile_core.py','sha256':sha(script)}]}
        (self.root/'docs').mkdir();(self.root/'docs/core-apk-inputs.json').write_text(json.dumps(manifest))
    def tearDown(self):self.temp.cleanup()
    def test_valid_boundary(self):self.assertEqual(module.check(self.root),1)
    def test_source_update_requires_repacking(self):
        (self.assets/'mobile_core.py').write_text('print("new")\n')
        with self.assertRaisesRegex(ValueError,'module is stale'):module.check(self.root)
    def test_missing_module_requires_repacking(self):
        (self.assets/'mobile_extra.py').write_text('pass\n')
        with self.assertRaisesRegex(ValueError,'module list is stale'):module.check(self.root)
    def test_jar_change_is_rejected(self):
        (self.root/'app/libs/Qt6Android.jar').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'Qt Java archive differs'):module.check(self.root)
    def test_native_change_is_rejected(self):
        (self.root/'app/src/main/jniLibs/arm64-v8a/libFixture.so').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'core library changed'):module.check(self.root)
    def test_runtime_change_is_rejected(self):
        (self.assets/'python-home.zip').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'archive changed'):module.check(self.root)
    def test_part_missing_material_resources_is_rejected(self):
        path=self.root/'docs/core-apk-inputs.json';manifest=json.loads(path.read_text());manifest['part']=True;path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'Part material resources are missing'):module.check(self.root)
    def test_sketcher_missing_native_registration_is_rejected(self):
        path=self.root/'docs/core-apk-inputs.json';manifest=json.loads(path.read_text());manifest['sketcher']=True;path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError,'Sketcher runtime registration/library is incomplete'):module.check(self.root)
if __name__=='__main__':unittest.main()
