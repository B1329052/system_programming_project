// test03: 位元運算與邏輯運算
int main() {
    int a = 12;
    int b = 10;

    printf("a & b  = %d\n", a & b);
    printf("a | b  = %d\n", a | b);
    printf("a ^ b  = %d\n", a ^ b);
    printf("a << 2 = %d\n", a << 2);
    printf("b >> 1 = %d\n", b >> 1);

    printf("!0 = %d\n", !0);
    printf("!5 = %d\n", !5);

    int c = 1;
    int d = 0;
    printf("c && d = %d\n", c && d);
    printf("c || d = %d\n", c || d);

    return 0;
}
