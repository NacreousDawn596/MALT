A = [1 2];
try
    x = A(5);
catch err
    msg = err.message;
    ident = err.identifier;
end
