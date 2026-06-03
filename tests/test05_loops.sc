// test05: while / for / do-while 迴圈與 break/continue
int main() {
    // while 迴圈：計算 1+2+...+10
    int sum = 0;
    int i = 1;
    while (i <= 10) {
        sum += i;
        i += 1;
    }
    printf("sum(1..10) = %d\n", sum);

    // for 迴圈：印出偶數
    printf("even: ");
    for (int j = 2; j <= 10; j += 2) {
        printf("%d ", j);
    }
    printf("\n");

    // do-while 迴圈
    int count = 0;
    do {
        count += 1;
    } while (count < 5);
    printf("do-while count = %d\n", count);

    // break 測試
    int k = 0;
    while (1) {
        if (k == 3) {
            break;
        }
        k += 1;
    }
    printf("break at k = %d\n", k);

    // continue 測試：跳過 3 的倍數
    printf("skip multiples of 3: ");
    for (int m = 1; m <= 10; m += 1) {
        if (m % 3 == 0) {
            continue;
        }
        printf("%d ", m);
    }
    printf("\n");

    return 0;
}
