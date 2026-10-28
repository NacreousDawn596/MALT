n = 100000;
v = zeros(1, n);
total = 0;

for k = 1:n
    v(k) = k;
    total = total + v(k);
end

disp(total);
