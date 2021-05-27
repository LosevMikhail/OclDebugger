import unittest

from primitives import Variable, VarDeclaration, StructDeclaration, FieldDeclaration, ClTypes


class VariableTest(unittest.TestCase):
    def setUp(self) -> None:
        s1, s2 = StructDeclaration(None), StructDeclaration(None)
        arr1dstruct, arr2dstruct, arr3dstruct = StructDeclaration(None), StructDeclaration(None), StructDeclaration(
            None)

        s1.name = 'my_struct_1'
        s1.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'double2')}

        s2.name = 'my_struct_2'
        s2.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'my_struct_1')}

        arr1dstruct.name = 'my_struct_3'
        arr1dstruct.fields = {'count': FieldDeclaration('count', 'int'),
                              'a': FieldDeclaration('a', 'int [3]')}

        arr2dstruct.name = 'my_struct_4'
        arr2dstruct.fields = {'count': FieldDeclaration('count', 'int'),
                              'a': FieldDeclaration('a', 'int [3] [2]')}

        arr3dstruct.name = 'my_struct_5'
        arr3dstruct.fields = {'count': FieldDeclaration('count', 'int'),
                              'a': FieldDeclaration('a', 'int [3] [2] [1]')}

        ClTypes.struct_declarations = [s1, s2, arr1dstruct, arr2dstruct, arr3dstruct]

    def tearDown(self) -> None:
        pass

    def test_char_positive(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private char'),
                       value='a 12')
        self.assertEqual(var.value, 0x12)

    def test_char_negative(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private char'),
                       value='a ff')
        self.assertEqual(var.value, -1)

    def test_char_prefix(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private char'),
                       value='a 0x70')
        self.assertEqual(var.value, 0x70)

    def test_char_too_much_digits(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private char'),
                       value='a 0x1f100')
        self.assertEqual(var.value, 0x00)

    def test_uchar_positive(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private uchar'),
                       value='a 12')
        self.assertEqual(var.value, 0x12)

    def test_uchar_negative(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private uchar'),
                       value='a ff')
        self.assertEqual(var.value, 255)

    def test_uchar_prefix(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private uchar'),
                       value='a 0x70')
        self.assertEqual(var.value, 0x70)

    def test_uchar_too_much_digits(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private uchar'),
                       value='a 0x1f100')
        self.assertEqual(var.value, 0x00)

    def test_int(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int'),
                       value='a 0x141')
        self.assertEqual(var.value, 0x141)

    def test_int_too_much_digits(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int'),
                       value='a 0x777777111111ff')
        self.assertEqual(var.value, 0x111111ff)

    def test_1d_arr(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int [3]'),
                       value='a 0xffffffff 1 2 3')
        self.assertEqual(var.value,
                         (0xffffffff, [1, 2, 3])
                         )

    def test_float_positive(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private float'),
                       value='a 0.1')
        self.assertAlmostEqual(var.value, 0.1)

    def test_float_negative(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private float'),
                       value='a -0.133')
        self.assertAlmostEqual(var.value, -0.133)

    def test_double_positive(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double'),
                       value='a 0.1')
        self.assertAlmostEqual(var.value, 0.1)

    def test_double_negative(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double'),
                       value='a -0.133')
        self.assertAlmostEqual(var.value, -0.133)

    def test_double2(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double2'),
                       value='a -0.133,0.1')
        expected = [-0.133, 0.1]
        self.assertEqual(len(var.value), len(expected))
        for a, e in zip(var.value, expected):
            self.assertAlmostEqual(a, e)

    def test_double4(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double4'),
                       value='a -0.133,0.1,0.2,0.3')
        expected = [-0.133, 0.1, 0.2, 0.3]
        self.assertEqual(len(var.value), len(expected))
        for a, e in zip(var.value, expected):
            self.assertAlmostEqual(a, e)

    def test_double8(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double8'),
                       value='a -0.133,0.1,0.2,0.3,-0.133,0.1,0.2,0.7')
        expected = [-0.133, 0.1, 0.2, 0.3, -0.133, 0.1, 0.2, 0.7]
        self.assertEqual(len(var.value), len(expected))
        for a, e in zip(var.value, expected):
            self.assertAlmostEqual(a, e)

    def test_double16(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private double16'),
                       value='a -0.133,0.1,0.2,0.3,-0.133,0.1,0.2,0.7,-0.133,0.1,0.2,0.3,-0.133,0.1,0.2,0.7')
        expected = [-0.133, 0.1, 0.2, 0.3, -0.133, 0.1, 0.2, 0.7, -0.133, 0.1, 0.2, 0.3, -0.133, 0.1, 0.2, 0.7]
        self.assertEqual(len(var.value), len(expected))
        for a, e in zip(var.value, expected):
            self.assertAlmostEqual(a, e)

    def test_2d_arr(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int [3] [2]'),
                       value='a 0x00000000 0x00000000 1 2 0x00000008 3 4 0x0000000C 5 6')
        self.assertEqual(var.value, (0x00000000, [(0x00000000, [1, 2]), (0x00000008, [3, 4]), (0x0000000C, [5, 6])]))

    def test_3d_arr(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int [3] [2] [1]'),
                       value='a 0x00000000 0x00000000 0x00000000 1 0x00000004 2 0x00000008 0x00000008 3 0x0000000C 4 0x00000010 0x00000010 5 0x00000014 6')
        self.assertEqual(var.value, (0x00000000, [(0x00000000, [(0x00000000, [1]), (0x00000004, [2])]),
                                                  (0x00000008, [(0x00000008, [3]), (0x0000000C, [4])]),
                                                  (0x00000010, [(0x00000010, [5]), (0x00000014, [6])])]))

    def test_simple_struct1(self):
        var = Variable(decl=VarDeclaration(var_name='s', full_type='__private my_struct_1'),
                       value='s count 0x1488 v 0.1,0.2')
        self.assertEqual(var.value, {'count': 0x1488, 'v': [0.1, 0.2]})

    def test_simple_struct2(self):
        var = Variable(decl=VarDeclaration(var_name='s', full_type='__private my_struct_1'),
                       value='s count 0x145 v 0.1,0.3')
        self.assertEqual(var.value, {'count': 0x145, 'v': [0.1, 0.3]})

    def test_struct_with_struct_as_a_field(self):
        var = Variable(decl=VarDeclaration(var_name='s', full_type='__private my_struct_2'),
                       value='s count 0x145 v count 0x231 v 0.1,0.3')
        self.assertEqual(var.value, {'count': 0x145, 'v': {'count': 0x231, 'v': [0.1, 0.3]}})

    def test_array1d_struct(self):
        var = Variable(decl=VarDeclaration(var_name='s', full_type='__private my_struct_3'),
                       value='s count 0x1488 a 0x00000000 0x71 0x198 0x43')
        self.assertEqual(var.value, {'count': 0x1488, 'a': (0, [0x71, 0x198, 0x43])})

    def test_array2d_struct(self):
        var = Variable(decl=VarDeclaration(var_name='s', full_type='__private my_struct_5'),
                       value='s count 0x1488 a 0x00000000 0x00000000 0x00000000 1 0x00000004 2 0x00000008 0x00000008 3 0x0000000C 4 0x00000010 0x00000010 5 0x00000014 6')
        self.assertEqual(var.value,
                         {'count': 0x1488, 'a': (0x00000000, [(0x00000000, [(0x00000000, [1]), (0x00000004, [2])]),
                                                              (0x00000008, [(0x00000008, [3]), (0x0000000C, [4])]),
                                                              (0x00000010, [(0x00000010, [5]), (0x00000014, [6])])])})


if __name__ == "__main__":
    unittest.main()
