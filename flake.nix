{
  description = "MALT — a MATLAB-compatible language runtime powered by CPython";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/f4b794aaffc0e3d45da81088d492b118224bb476";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        python = pkgs.python313;
        pythonPackages = pkgs.python313Packages;

        # Matplotlib built with interactive GUI backends (Qt5 + Tk) so that
        # desktop figure windows work when a display server is available.
        matplotlibWithGui = pythonPackages.matplotlib.override {
          enableQt = true;
          enableTk = true;
        };

        pythonDeps = ps: with ps; [
          numpy
          scipy
          matplotlibWithGui
          pytest
          hypothesis
          ruff
          mypy
        ];

        pythonEnv = python.withPackages pythonDeps;

        # Installable wrapper: exposes `malt` (and its dependencies) without
        # touching the host system. Point PYTHONPATH at the bundled source.
        maltPackage = pkgs.stdenv.mkDerivation {
          pname = "malt";
          version = "0.1.0";
          src = self;
          buildInputs = [ pythonEnv ];
          buildPhase = "true";
          installPhase = ''
            mkdir -p "$out/bin"
            cat > "$out/bin/malt" <<EOF
            #!${pkgs.runtimeShell}
            export PYTHONPATH="\$PWD/src:\$PYTHONPATH"
            export MPLBACKEND="\''${MPLBACKEND:-Agg}"
            exec ${pythonEnv}/bin/python -m malt "\$@"
            EOF
            chmod +x "$out/bin/malt"
          '';
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.git
          ];
          shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            # Headless by default so tests never require a display. Override
            # with `export MPLBACKEND=Qt5Agg` for interactive figure windows.
            export MPLBACKEND=Agg
            echo "MALT development shell (nixpkgs ${nixpkgs.lib.version})"
            echo "  python:      $(python --version 2>&1)"
            echo "  run tests:   nix develop -c pytest"
            echo "  run MALT:    nix develop -c python -m malt --help"
          '';
        };

        packages.default = maltPackage;
      });
}
