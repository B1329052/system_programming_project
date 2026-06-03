// test10: 指標操作（取址、解參照、指標傳參交換）
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main() {
    int x = 10;
    int y = 20;

    // 取址與解參照
    int *p = &x;
    printf("x = %d\n", x);
    printf("*p = %d\n", *p);

    // 透過指標修改值
    *p = 99;
    printf("after *p = 99, x = %d\n", x);

    // 指標傳參交換
    int a = 100;
    int b = 200;
    printf("before swap: a=%d, b=%d\n", a, b);
    swap(&a, &b);
    printf("after swap:  a=%d, b=%d\n", a, b);

    return 0;
}
