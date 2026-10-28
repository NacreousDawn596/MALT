n = 100000;
total = 0;

for k = 1:n
    total = total + k * k + 2 * k - 1;
end

disp(total);
