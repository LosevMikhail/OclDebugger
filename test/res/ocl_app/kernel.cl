struct my_struct {
	uint count[2][2];
	double2 w1;
};

struct my_struct2 {
	struct my_struct a;
	double w2;
};

__kernel void test(__global int* message, __global char* debuggingBuffer)
{
    char c = 1;
    uchar uc = 2;
    short s = 3;
    ushort us = 4;
    int i = 5;
    uint ui = 6;
    long l = 7;
    ulong ul = 8;
    float f = 14.31;
    double d = -147.1;

	int arr_1d[2] = {14, 17};
    int arr_2d[2][2] = {{14, 17}, {15, 31}};
    int arr_3d[2][2][2] = {{{14, 17}, {15, 31}}, {{1, 2}, {3, 4}}};

    struct my_struct s1 = {{{14, 17}, {15, 31}}, (double2)(0.1, 0.2)};
    struct my_struct2 s2 = {{{{14, 17}, {15, 31}}, (double2)(0.1, 0.2)}, 0.12};





}

