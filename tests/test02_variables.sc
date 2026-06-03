// test02: 變數宣告、賦值與複合指定運算
int main() {
    int x = 100;
    int y;
    y = x + 50;
    printf("x = %d\n", x);
    printf("y = %d\n", y);

    x += 10;
    printf("x += 10 -> %d\n", x);
    x -= 20;
    printf("x -= 20 -> %d\n", x);
    x *= 2;
    printf("x *= 2  -> %d\n", x);
    x /= 3;
    printf("x /= 3  -> %d\n", x);
    x %= 7;
    printf("x %%= 7  -> %d\n", x);

    return 0;
}
