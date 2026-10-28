A = rand(100, 100);
total = 0;

for k = 1:100
    total = total + A(k, k);
end

disp(total);
