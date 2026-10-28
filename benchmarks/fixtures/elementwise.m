x = linspace(0, 10, 100000);
y = sin(x) + cos(x);
z = y.^2;
disp(numel(z));
