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






 int _losev_target_threads[] = {0};
 if (get_global_id(0) == *_losev_target_threads) { printf("[ debugging output begins ]\n"); } 
 
 for (int _losev_thread_counter = 0; _losev_thread_counter < 1; _losev_thread_counter++) {
 	if (get_global_id(0) == _losev_target_threads[_losev_thread_counter]) { // Save debugging data
 		int _losev_i = 0; int _losev_j = 0; int _losev_k = 0;
 		printf("c ");printf("%x \n", c);
 		
 		printf("uc ");printf("%x \n", uc);
 		
 		printf("s ");printf("%hx \n", s);
 		
 		printf("us ");printf("%hx \n", us);
 		
 		printf("i ");printf("%x \n", i);
 		
 		printf("ui ");printf("%x \n", ui);
 		
 		printf("l ");printf("%lx \n", l);
 		
 		printf("ul ");printf("%lx \n", ul);
 		
 		printf("f ");printf("%f \n", f);
 		
 		printf("d ");printf("%lf \n", d);
 		
 		printf("arr_1d ");printf("%x", arr_1d);
 		_losev_i = 0;
 		while (_losev_i < 2) {
 			printf(" ");
 			printf("%x", arr_1d[_losev_i]);
 			_losev_i++;
 		}
 		printf("\n");
 		printf("arr_2d ");printf("%x", arr_2d);
 		_losev_i = 0;
 		while (_losev_i < 2) {
 			printf(" %x", arr_2d[_losev_i]);
 			_losev_j = 0;
 			while (_losev_j < 2) {
 				printf(" ");
 				printf("%x", arr_2d[_losev_i][_losev_j]);
 				_losev_j++;
 			}
 			_losev_i++;
 		}
 		printf("\n");
 		printf("arr_3d ");printf("%x", arr_3d);
 		_losev_i = 0;
 		while (_losev_i < 2) {
 			printf(" %x", arr_3d[_losev_i]);
 			_losev_j = 0;
 			while (_losev_j < 2) {
 				printf(" %x", arr_3d[_losev_i][_losev_j]);
 				_losev_k = 0;
 				while (_losev_k < 2) {
 					printf(" ");
 					printf("%x", arr_3d[_losev_i][_losev_j][_losev_k]);
 					_losev_k++;
 				}
 				_losev_j++;
 			}
 			_losev_i++;
 		}
 		printf("\n");
 		printf("s1 ");printf("count ");printf("%x", s1.count);
 		_losev_i = 0;
 		while (_losev_i < 2) {
 			printf(" %x", s1.count[_losev_i]);
 			_losev_j = 0;
 			while (_losev_j < 2) {
 				printf(" ");
 				printf("%x", s1.count[_losev_i][_losev_j]);
 				_losev_j++;
 			}
 			_losev_i++;
 		}
 		printf(" ");printf("w1 ");printf("%v2lf ", s1.w1);
 		printf("\n");
 		printf("s2 ");printf("a ");printf("count ");printf("%x", s2.a.count);
 		_losev_i = 0;
 		while (_losev_i < 2) {
 			printf(" %x", s2.a.count[_losev_i]);
 			_losev_j = 0;
 			while (_losev_j < 2) {
 				printf(" ");
 				printf("%x", s2.a.count[_losev_i][_losev_j]);
 				_losev_j++;
 			}
 			_losev_i++;
 		}
 		printf(" ");printf("w1 ");printf("%v2lf ", s2.a.w1);
 		printf("");printf("w2 ");printf("%lf ", s2.w2);
 		printf("\n");
 	} // Save debugging data
 } // ?

	


//	message[gid] += gid;
}

