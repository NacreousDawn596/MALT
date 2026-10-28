function dydt = decay(t, y)
    dydt = -2*y;
end

[t, y] = ode45(@decay, [0 5], 1);
disp(y(end));
