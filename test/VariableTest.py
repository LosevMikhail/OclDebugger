import unittest

from primitives import Variable, VarDeclaration


class VariableTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_int(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int'),
                       value='a 0x141')
        self.assertEqual(var.value, 0x141)

    def test_1d_arr(self):
        var = Variable(decl=VarDeclaration(var_name='a', full_type='__private int [3]'),
                       value='a 0xffffffff 1 2 3')
        self.assertEqual(var.value,
                         (0xffffffff, [1, 2, 3])
                         )

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
