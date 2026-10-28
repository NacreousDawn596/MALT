x = linspace(0, 2*pi, 100);

figure(1);

plot(x, sin(x), 'r-');
hold on;

plot(x, cos(x), 'b--');

hold off;

legend('sin(x)', 'cos(x)');
title('Trigonometric Functions');
