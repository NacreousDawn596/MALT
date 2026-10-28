x = linspace(0, 10, 100);

figure(1);

subplot(2, 1, 1);
plot(x, x.^2);
title('Square');

subplot(2, 1, 2);
plot(x, sqrt(x));
title('Square Root');
