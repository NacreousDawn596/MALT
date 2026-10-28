n = 300;
total = 0;

for i = 1:n
    for j = 1:n
        total = total + i*j;
    end
end

disp(total);
