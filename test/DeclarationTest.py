import unittest

from primitives import VarDeclaration, StructDeclaration, FieldDeclaration, ClTypes


class VariableDeclarationTest(unittest.TestCase):
    def setUp(self) -> None:
        s1, s2 = StructDeclaration(None), StructDeclaration(None)

        s1.name = 'my_struct_1'
        s1.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'double2')}

        s2.name = 'my_struct_2'
        s2.fields = {'count': FieldDeclaration('count', 'int'),
                     'v': FieldDeclaration('v', 'my_struct_1')}

        ClTypes.struct_declarations = [s1, s2]

    def test_private_int1(self):
        v = VarDeclaration(var_name='a', full_type='__private int')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, False)
        self.assertEqual(v.var_shape, None)
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 2)
        self.assertEqual(v.is_struct(), False)

    def test_private_int2(self):
        v = VarDeclaration(var_name='a', full_type='int __private')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, False)
        self.assertEqual(v.var_shape, None)
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 2)
        self.assertEqual(v.is_struct(), False)

    def test_private_1d_array(self):
        v = VarDeclaration(var_name='a', full_type='__private int [41]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [41])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 43)
        self.assertEqual(v.is_struct(), False)

    def test_private_2d_array(self):
        v = VarDeclaration(var_name='a', full_type='__private int [41] [5]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [41, 5])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 248)
        self.assertEqual(v.is_struct(), False)

    def test_private_3d_array(self):
        v = VarDeclaration(var_name='a', full_type='__private int [2] [3] [1]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [2, 3, 1])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 16)
        self.assertEqual(v.is_struct(), False)

    def test_local_1d_array(self):
        v = VarDeclaration(var_name='a', full_type='__local int [41]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__local')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [41])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 43)
        self.assertEqual(v.is_struct(), False)

    def test_local_2d_array(self):
        v = VarDeclaration(var_name='a', full_type='__local int [41] [5]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__local')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [41, 5])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 248)
        self.assertEqual(v.is_struct(), False)

    def test_local_3d_array(self):
        v = VarDeclaration(var_name='a', full_type='__local int [2] [3] [1]')
        self.assertEqual(v.var_type, 'int')
        self.assertEqual(v.address_space, '__local')
        self.assertEqual(v.is_array, True)
        self.assertEqual(v.var_shape, [2, 3, 1])
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 16)
        self.assertEqual(v.is_struct(), False)

    def test_struct(self):
        v = VarDeclaration(var_name='a', full_type='__private struct my_struct_1')
        self.assertEqual(v.var_type, 'my_struct_1')
        self.assertEqual(v.address_space, '__private')
        self.assertEqual(v.is_array, False)
        self.assertEqual(v.var_shape, None)
        self.assertEqual(v.pointer_rank, 0)
        self.assertEqual(v.words_num(), 5)
        self.assertEqual(v.is_struct(), True)

    def test_undefined_struct(self):
        self.assertRaises(Exception, VarDeclaration(var_name='a', full_type='__private struct my_struct1'))



if __name__ == "__main__":
    unittest.main()