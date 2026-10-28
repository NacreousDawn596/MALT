x = linspace(0, 2*pi, 200);
y = sin(x);

figure(1);
plot(x, y, 'b-', 'LineWidth', 2);

title('Sine Wave');
xlabel('Time');
ylabel('Amplitude');

grid on;
