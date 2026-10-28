function y = sq(x)
    y = x * x;
end

n = 20000;
total = 0;

for k = 1:n
    total = total + sq(k);
end

disp(total);
