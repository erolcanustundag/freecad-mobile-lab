import importlib.util,re,unittest,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('catalog',ROOT/'scripts/localization_catalog.py')
catalog=importlib.util.module_from_spec(spec);spec.loader.exec_module(catalog)
def load(folder):return {x.attrib['name']:x.text for x in ET.parse(ROOT/'app/src/main/res'/folder/'strings.xml').getroot()}
class LocalizationTests(unittest.TestCase):
    def test_fallback_and_placeholders(self):
        english=load('values')
        for locale in ['values-tr','values-de']:
            translated=load(locale)
            self.assertGreaterEqual(len(translated),597)
            self.assertLessEqual(set(translated),set(english))
            for key,text in translated.items():
                self.assertTrue(text)
                self.assertEqual(re.findall(r'%[\d$.,+\-]*[sdfe]',english[key]),re.findall(r'%[\d$.,+\-]*[sdfe]',text),key)
    def test_entry_points_and_shared_preference(self):
        for locale in ['values-tr','values-de']:
            translated=load(locale)
            for text in ['Language','Use phone language','+ Create','Edit','Undo','Open','Export','Recovery','Restart lab','Run command','Save FCStd']:
                self.assertIn(catalog.key(text),translated)
        java=ROOT/'app/src/main/java/org/freecad/mobilelab'
        self.assertIn('new AtomicFile', (java/'L10n.java').read_text())
        self.assertNotIn('getText().toString().equals("Recovery")',(java/'CoreDocumentActivity.java').read_text())
        self.assertIn('CURVE_KINDS[kind.getSelectedItemPosition()]',(java/'SketchCanvas.java').read_text())
    def test_java_lexer_ignores_comments_and_character_quotes(self):
        self.assertEqual(list(catalog.literals('/* "bad" */ char c=\'"\'; String s="good"; // "bad"\n')),['good'])
if __name__=='__main__':unittest.main()
