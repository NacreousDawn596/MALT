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

        # Qt 5 base, for the Qt platform plugins (e.g. ``xcb``) that the
        # Qt5Agg backend needs at runtime. Nix does not expose this path on
        # its own, so we set ``QT_QPA_PLATFORM_PLUGIN_PATH`` explicitly below.
        qtbase = pkgs.libsForQt5.qtbase;

        # Qt 6 base, for the Qt6 GUI REPL (`malt gui`). Kept separate from the
        # Qt5 plugin path above because the two share ``libqxcb.so`` but are
        # ABI-incompatible; the GUI sets its own path at startup.
        qt6base = pkgs.qt6.qtbase;

        pythonDeps = ps: with ps; [
          numpy
          scipy
          matplotlibWithGui
          pyqt6
          pytest
          hypothesis
          ruff
          mypy
        ];

        pythonEnv = python.withPackages pythonDeps;

        # Installable package: bundles the source into the store and exposes a
        # `malt` wrapper (plus a `malt-gui` launcher). Depends only on the
        # store (never `$PWD` or the host environment).
        maltPackage = pkgs.stdenv.mkDerivation {
          pname = "malt";
          version = "0.4.4";
          src = self;
          buildInputs = [ pythonEnv ];
          buildPhase = "true";
          installPhase = ''
            mkdir -p "$out/lib"
            cp -r src/malt "$out/lib/malt"
            mkdir -p "$out/bin"
            cat > "$out/bin/malt" <<EOF
            #!${pkgs.runtimeShell}
            export PYTHONPATH="$out/lib:\''${PYTHONPATH:-}"
            export MPLBACKEND="\''${MPLBACKEND:-Qt5Agg}"
            export QT_QPA_PLATFORM_PLUGIN_PATH="${qtbase.bin}/${qtbase.qtPluginPrefix}/platforms"
            export MALT_QT6_PLUGIN_PATH="${qt6base}/${qt6base.qtPluginPrefix}/platforms"
            exec ${pythonEnv}/bin/python -m malt "\$@"
            EOF
            cat > "$out/bin/malt-gui" <<EOF
            #!${pkgs.runtimeShell}
            exec "$out/bin/malt" gui "\$@"
            EOF
            chmod +x "$out/bin/malt" "$out/bin/malt-gui"

            # Desktop entry + icon for the GUI.
            mkdir -p "$out/share/applications"
            cat > "$out/share/applications/malt.desktop" <<EOF
            [Desktop Entry]
            Type=Application
            Name=MALT
            Comment=Interactive notebook REPL for the MALT language
            Exec=malt-gui
            Icon=malt
            Terminal=false
            Categories=Development;Science;Math;
            EOF
            mkdir -p "$out/share/icons/hicolor/256x256/apps"
            cp assets/logo.png "$out/share/icons/hicolor/256x256/apps/malt.png"
          '';
          meta = {
            description = "A MATLAB-compatible language runtime powered by CPython";
            license = pkgs.lib.licenses.mit;
            homepage = "https://github.com/NacreousDawn596/MALT";
            mainProgram = "malt";
            platforms = pkgs.lib.platforms.unix;
          };
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pythonEnv
            pkgs.git
            # GNU Octave, for optional differential tests (tests/differential/).
            pkgs.octave
          ];
          shellHook = ''
            export PYTHONPATH="$PWD/src:$PYTHONPATH"
            # Headless by default so tests never require a display. Override
            # with `export MPLBACKEND=Qt5Agg` for interactive figure windows.
            export MPLBACKEND=''${MPLBACKEND:-Agg}
            # Qt platform plugins (xcb) for the Qt5Agg backend.
            export QT_QPA_PLATFORM_PLUGIN_PATH="${qtbase.bin}/${qtbase.qtPluginPrefix}/platforms"
            # Qt6 platform plugins, for the GUI REPL (`malt gui`), which sets
            # QT_QPA_PLATFORM_PLUGIN_PATH from this at startup.
            export MALT_QT6_PLUGIN_PATH="${qt6base}/${qt6base.qtPluginPrefix}/platforms"
            echo "MALT development shell (nixpkgs ${nixpkgs.lib.version})"
            echo "  python:      $(python --version 2>&1)"
            echo "  run tests:   nix develop -c pytest"
            echo "  run MALT:    nix develop -c python -m malt --help"
          '';
        };

        packages.default = maltPackage;
        apps.default = {
          type = "app";
          program = "${maltPackage}/bin/malt";
        };
        apps.gui = {
          type = "app";
          program = "${maltPackage}/bin/malt-gui";
        };
      });
}
