// test08: 遞迴求最大公因數 (GCD) 與冪次方
int gcd(int a, int b) {
    if (b == 0) {
        return a;
    }
    return gcd(b, a % b);
}

int power(int base, int exp) {
    if (exp == 0) {
        return 1;
    }
    return base * power(base, exp - 1);
}

int main() {
    printf("gcd(48, 18) = %d\n", gcd(48, 18));
    printf("gcd(100, 75) = %d\n", gcd(100, 75));
    printf("gcd(17, 13) = %d\n", gcd(17, 13));

    printf("2^10 = %d\n", power(2, 10));
    printf("3^5  = %d\n", power(3, 5));
    printf("5^0  = %d\n", power(5, 0));

    return 0;
}
