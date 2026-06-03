// test06: 函式定義與呼叫
int square(int x) {
    return x * x;
}

int add(int a, int b) {
    return a + b;
}

int max_of_three(int a, int b, int c) {
    int m = a;
    if (b > m) {
        m = b;
    }
    if (c > m) {
        m = c;
    }
    return m;
}

int main() {
    printf("square(7) = %d\n", square(7));
    printf("add(3, 4) = %d\n", add(3, 4));
    printf("max_of_three(5, 9, 2) = %d\n", max_of_three(5, 9, 2));

    int result = square(add(2, 3));
    printf("square(add(2,3)) = %d\n", result);

    return 0;
}
