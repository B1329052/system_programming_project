// test07: 遞迴呼叫（階乘與費氏數列）
int factorial(int n) {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

int fibonacci(int n) {
    if (n <= 0) {
        return 0;
    }
    if (n == 1) {
        return 1;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    printf("5! = %d\n", factorial(5));
    printf("7! = %d\n", factorial(7));
    printf("10! = %d\n", factorial(10));

    printf("fib(0) = %d\n", fibonacci(0));
    printf("fib(1) = %d\n", fibonacci(1));
    printf("fib(7) = %d\n", fibonacci(7));
    printf("fib(10) = %d\n", fibonacci(10));

    return 0;
}
