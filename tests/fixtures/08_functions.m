function [s, p] = calculate(a, b)
    s = a + b;
    p = a * b;
end

[x, y] = calculate(3, 4);

disp(x);
disp(y);
