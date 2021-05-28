import unittest
from shutil import copyfile

from OclDebugger import OclDebugger


class OclDebuggerTest(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def test_it_all(self):
        debugger = OclDebugger(
            kernel_file='res/ocl_app/kernel.cl',
            binary='res/ocl_app/app',
            build_cmd=None  # This application doesnt need rebuilding
        )

        variables = debugger.safe_debug(break_line=35, threads=[0])
        c = variables[0]
        self.assertEqual(c.decl.var_name, 'c')
        self.assertEqual(c.value, 1)

        uc = variables[1]
        self.assertEqual(uc.decl.var_name, 'uc')
        self.assertEqual(uc.value, 2)

        s = variables[2]
        self.assertEqual(s.decl.var_name, 's')
        self.assertEqual(s.value, 3)

        us = variables[3]
        self.assertEqual(us.decl.var_name, 'us')
        self.assertEqual(us.value, 4)

        i = variables[4]
        self.assertEqual(i.decl.var_name, 'i')
        self.assertEqual(i.value, 5)

        ui = variables[5]
        self.assertEqual(ui.decl.var_name, 'ui')
        self.assertEqual(ui.value, 6)

        l = variables[6]
        self.assertEqual(l.decl.var_name, 'l')
        self.assertEqual(l.value, 7)


        ul = variables[7]
        self.assertEqual(ul.decl.var_name, 'ul')
        self.assertEqual(ul.value, 8)


        f = variables[8]
        self.assertEqual(f.decl.var_name, 'f')
        self.assertAlmostEqual(f.value, 14.31, delta=0.00001)

        d = variables[9]
        self.assertEqual(d.decl.var_name, 'd')
        self.assertAlmostEqual(d.value, -147.1, delta=0.00001)

        arr_1d = variables[10]
        self.assertEqual(arr_1d.decl.var_name, 'arr_1d')
        self.assertEqual(arr_1d.value[1], [14, 17])

        arr_2d = variables[11]
        self.assertEqual(arr_2d.decl.var_name, 'arr_2d')
        self.assertEqual(arr_2d.value[1][0][1], [14, 17])
        self.assertEqual(arr_2d.value[1][1][1], [15, 31])

        arr_3d = variables[12]
        self.assertEqual(arr_3d.decl.var_name, 'arr_3d')
        self.assertEqual(arr_3d.value[1][0][1][0][1], [14, 17])
        self.assertEqual(arr_3d.value[1][0][1][1][1], [15, 31])
        self.assertEqual(arr_3d.value[1][1][1][0][1], [1, 2])
        self.assertEqual(arr_3d.value[1][1][1][1][1], [3, 4])

        s1 = variables[13]
        self.assertEqual(s1.decl.var_name, 's1')
        arr_2d = s1.value['count']
        self.assertEqual(arr_2d[1][0][1], [14, 17])
        self.assertEqual(arr_2d[1][1][1], [15, 31])
        self.assertEqual(s1.value['w1'], [0.1, 0.2])

        s2 = variables[14]
        self.assertEqual(s2.decl.var_name, 's2')
        s1 = s2.value['a']
        arr_2d = s1['count']
        self.assertEqual(arr_2d[1][0][1], [14, 17])
        self.assertEqual(arr_2d[1][1][1], [15, 31])
        self.assertEqual(s1['w1'], [0.1, 0.2])
        self.assertEqual(s2.value['w2'], 0.12)


if __name__ == "__main__":
    unittest.main()
