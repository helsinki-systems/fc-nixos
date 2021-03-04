# Copyright (c) 2011 gocept gmbh & co. kg
# See also LICENSE.txt

from fc.util.configfile import ConfigFile
import io
import os
import os.path
import tempfile
import unittest


class TestConfigFile(unittest.TestCase):

    def setUp(self):
        self.tf = tempfile.NamedTemporaryFile(suffix='test_configfile',
                                              delete=False)
        self.diffout = io.StringIO()

    def tearDown(self):
        try:
            os.unlink(self.tf.name)
        except OSError:
            pass

    def test_configfile_behaves_stringio_like(self):
        c = ConfigFile('filename')
        print('hello world', file=c)
        self.assertEqual(c.getvalue(), 'hello world\n')

    def test_create_file(self):
        os.unlink(self.tf.name)
        c = ConfigFile(self.tf.name, stdout=self.diffout)
        print('hello world', file=c)
        self.assertRaises(OSError, os.stat, self.tf.name)
        c.commit()
        self.assertEqual(open(self.tf.name).read(), 'hello world\n')

    def test_modify_file(self):
        with open(self.tf.name, 'w') as f:
            print('old file contents', file=f)
        c = ConfigFile(self.tf.name, stdout=self.diffout)
        print('hello world', file=c)
        changed = c.commit()
        self.assertTrue(changed, 'commit() did not set changed flag')
        self.assertEqual(open(self.tf.name).read(), 'hello world\n')

    def test_print_diff(self):
        with open(self.tf.name, 'w') as f:
            print('hello world 0\nhello world 1', file=f)
        c = ConfigFile(self.tf.name, stdout=self.diffout)
        print('hello world 1', file=c)
        print('hello world 2', file=c)
        c.commit()
        self.assertEqual(self.diffout.getvalue(), """\
--- {fn} (old)
+++ {fn} (new)
@@ -1,2 +1,2 @@
-hello world 0
 hello world 1
+hello world 2
""".format(fn=self.tf.name))

    def test_dont_touch_unchanged(self):
        with open(self.tf.name, 'w') as f:
            print('hello world', file=f)
        before = os.stat(self.tf.name)
        c = ConfigFile(self.tf.name, self.diffout)
        print('hello world', file=c)
        changed = c.commit()
        self.assertFalse(changed, "commit() set changed flag but shouldn't")
        after = os.stat(self.tf.name)
        self.assertEqual(before, after)
        self.assertEqual('', self.diffout.getvalue())
