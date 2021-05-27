import unittest

from primitives import Variable, VarDeclaration


class VariableTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

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


if __name__ == "__main__":
    unittest.main()
