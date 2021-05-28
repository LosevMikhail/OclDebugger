import unittest
from PrintfInserter import PrintfInserter

from primitives import VarDeclaration, StructDeclaration, FieldDeclaration, ClTypes


class InsertionTest(unittest.TestCase):
    def setUp(self) -> None:
        s1, s2 = StructDeclaration(None), StructDeclaration(None)

        s1.name = 'my_struct_1'
        s1.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'double2')}

        s2.name = 'my_struct_2'
        s2.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'my_struct_1')}

        ClTypes.struct_declarations = [s1, s2]

    def test_char(self):
        decl = VarDeclaration('a', '__private char')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%x \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_uchar(self):
        decl = VarDeclaration('a', '__private uchar')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%x \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_short(self):
        decl = VarDeclaration('a', '__private short')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%hx \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_ushort(self):
        decl = VarDeclaration('a', '__private ushort')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%hx \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_int(self):
        decl = VarDeclaration('a', '__private int')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%x \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_uint(self):
        decl = VarDeclaration('a', '__private uint')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%x \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_long(self):
        decl = VarDeclaration('a', '__private long')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%lx \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_ulong(self):
        decl = VarDeclaration('a', '__private ulong')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%lx \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_float(self):
        decl = VarDeclaration('a', '__private float')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%f \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_double(self):
        decl = VarDeclaration('a', '__private double')
        actual = PrintfInserter.generate_printf(decl)
        expected = 'printf("a ");printf("%lf \\n", a);\n'
        self.assertEqual(expected, actual)

    def test_1d_arr(self):
        decl = VarDeclaration('a', '__private int [2]')
        actual = PrintfInserter.generate_printf(decl)
        expected = '''printf("a ");printf("%x", a);
_losev_i = 0;
while (_losev_i < 2) {
	printf(" ");
	printf("%x", a[_losev_i]);
	_losev_i++;
}
printf("\\n");'''
        self.assertEqual(expected, actual)

    def test_2d_arr(self):
        decl = VarDeclaration('a', '__private int [2][3]')
        actual = PrintfInserter.generate_printf(decl)
        expected = '''printf("a ");printf("%x", a);
_losev_i = 0;
while (_losev_i < 2) {
	printf(" %x", a[_losev_i]);
	_losev_j = 0;
	while (_losev_j < 3) {
		printf(" ");
		printf("%x", a[_losev_i][_losev_j]);
		_losev_j++;
	}
	_losev_i++;
}
printf("\\n");'''
        self.assertEqual(expected, actual)


    def test_3d_arr(self):
        decl = VarDeclaration('a', '__private int [2][3][4]')
        actual = PrintfInserter.generate_printf(decl)
        expected = '''printf("a ");printf("%x", a);
_losev_i = 0;
while (_losev_i < 2) {
	printf(" %x", a[_losev_i]);
	_losev_j = 0;
	while (_losev_j < 3) {
		printf(" %x", a[_losev_i][_losev_j]);
		_losev_k = 0;
		while (_losev_k < 4) {
			printf(" ");
			printf("%x", a[_losev_i][_losev_j][_losev_k]);
			_losev_k++;
		}
		_losev_j++;
	}
	_losev_i++;
}
printf("\\n");'''
        self.assertEqual(expected, actual)

    def test_simple_struct(self):
        decl = VarDeclaration('a', '__private my_struct_1')
        actual = PrintfInserter.generate_printf(decl)
        expected = '''printf("a ");printf("count ");printf("%x ", a.count);
printf("v ");printf("%v2lf ", a.v);
printf("\\n");'''
        self.assertEqual(expected, actual)

    def test_compl_struct(self):
        decl = VarDeclaration('a', '__private my_struct_2')
        actual = PrintfInserter.generate_printf(decl)
        expected = '''printf("a ");printf("count ");printf("%x ", a.count);
printf("v ");printf("count ");printf("%x ", a.v.count);
printf("v ");printf("%v2lf ", a.v.v);
printf("");printf("\\n");'''
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
