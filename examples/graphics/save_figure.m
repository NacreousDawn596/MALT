x = 0:0.1:10;

figure(1);
plot(x, x.^2);

saveas(gcf, 'test_plot.png');
