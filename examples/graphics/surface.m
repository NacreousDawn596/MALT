x = linspace(-2, 2, 30);
y = linspace(-2, 2, 30);

[X, Y] = meshgrid(x, y);

Z = sin(sqrt(X.^2 + Y.^2));

figure(1);

surf(X, Y, Z);

xlabel('X');
ylabel('Y');
zlabel('Z');

title('3D Surface');
colorbar;
