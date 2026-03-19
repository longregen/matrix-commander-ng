{
  description = "matrix-commander-ng — CLI-based Matrix client for sending, receiving, and more";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    crane.url = "github:ipetkov/crane";
  };

  outputs = { self, nixpkgs, crane }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = fn: nixpkgs.lib.genAttrs systems fn;

      mkPkgsFor = system: import nixpkgs {
        inherit system;
        config.permittedInsecurePackages = [ "olm-3.2.16" ];
      };

      mkRustSrc = { pkgs, craneLib }: pkgs.lib.cleanSourceWith {
        src = craneLib.path ./.;
        filter = path: type:
          let baseName = builtins.baseNameOf path; in
            type == "directory" ||
            pkgs.lib.hasSuffix ".rs" baseName ||
            pkgs.lib.hasSuffix ".toml" baseName ||
            baseName == "Cargo.lock";
      };

      # Build the package for any system
      mkPackage = system:
        let
          pkgs = mkPkgsFor system;
          craneLib = crane.mkLib pkgs;

          rustSrc = mkRustSrc { inherit pkgs craneLib; };

          commonMeta = {
            description = "CLI-based Matrix client for sending, receiving, and more";
            mainProgram = "matrix-commander-ng";
            license = pkgs.lib.licenses.gpl3Plus;
          };

          releaseArgs = {
            src = rustSrc;
            pname = "matrix-commander-ng";
            version = "1.0.0";
            nativeBuildInputs = with pkgs; [ pkg-config ];
            buildInputs = pkgs.lib.optionals pkgs.stdenv.isDarwin
              (with pkgs.darwin.apple_sdk.frameworks; [ Security SystemConfiguration ]);
          };

          releaseArtifacts = craneLib.buildDepsOnly releaseArgs;
        in
        craneLib.buildPackage (releaseArgs // {
          cargoArtifacts = releaseArtifacts;
          meta = commonMeta;
        });

    in
    {
      # Packages for all platforms
      packages = forAllSystems (system: {
        default = mkPackage system;
        matrix-commander-ng = mkPackage system;
      } // nixpkgs.lib.optionalAttrs (system == "x86_64-linux") (
        let
          pkgs = mkPkgsFor system;
          craneLib = crane.mkLib pkgs;

          rustSrc = mkRustSrc { inherit pkgs craneLib; };

          ciArgs = {
            src = rustSrc;
            pname = "matrix-commander-ng";
            version = "1.0.0";
            nativeBuildInputs = with pkgs; [ pkg-config mold clang ];
            CARGO_PROFILE = "ci";
            CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER = "clang";
            CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS = "-C link-arg=-fuse-ld=mold";
          };
          ciArtifacts = craneLib.buildDepsOnly ciArgs;
          matrix-commander-ng-ci = craneLib.buildPackage (ciArgs // {
            cargoArtifacts = ciArtifacts;
            meta.mainProgram = "matrix-commander-ng";
          });

          integration-test = import ./tests/nixos-test.nix {
            inherit pkgs;
            inherit (pkgs) lib;
            matrix-commander-ng = matrix-commander-ng-ci;
          };

          equalization-test = import ./equalizing/tests/nixos-test.nix {
            inherit pkgs;
            inherit (pkgs) lib;
            matrix-commander-ng-local = matrix-commander-ng-ci;
          };

        in {
          pages-site = pkgs.stdenvNoCC.mkDerivation {
            name = "matrix-commander-ng-pages-site";
            dontUnpack = true;
            nativeBuildInputs = [ pkgs.python3 ];

            buildPhase = ''
              mkdir -p $out
              cp ${equalization-test}/comparison.json $out/
              cp ${equalization-test}/parity-summary.json $out/
              cp ${integration-test}/test-summary.json $out/
              cp ${./logos/matrix-commander-ng.svg} $out/logo.svg
              python3 ${./scripts/generate-site.py} \
                --comparison ${equalization-test}/comparison.json \
                --parity ${equalization-test}/parity-summary.json \
                --summary ${integration-test}/test-summary.json \
                --output-dir $out
            '';

            installPhase = "true";
          };
        }
      ));

      checks = forAllSystems (system: {}
        // nixpkgs.lib.optionalAttrs (system == "x86_64-linux") (
          let
            pkgs = mkPkgsFor system;
            craneLib = crane.mkLib pkgs;

            rustSrc = mkRustSrc { inherit pkgs craneLib; };

            ciArgs = {
              src = rustSrc;
              pname = "matrix-commander-ng";
              version = "1.0.0";
              nativeBuildInputs = with pkgs; [ pkg-config mold clang ];
              CARGO_PROFILE = "ci";
              CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_LINKER = "clang";
              CARGO_TARGET_X86_64_UNKNOWN_LINUX_GNU_RUSTFLAGS = "-C link-arg=-fuse-ld=mold";
            };
            ciArtifacts = craneLib.buildDepsOnly ciArgs;
            matrix-commander-ng-ci = craneLib.buildPackage (ciArgs // {
              cargoArtifacts = ciArtifacts;
              meta.mainProgram = "matrix-commander-ng";
            });
          in {
            integration-test = import ./tests/nixos-test.nix {
              inherit pkgs;
              inherit (pkgs) lib;
              matrix-commander-ng = matrix-commander-ng-ci;
            };
          }
        )
      );

      devShells = forAllSystems (system:
        let pkgs = mkPkgsFor system;
        in {
          default = pkgs.mkShell {
            name = "matrix-commander-ng";
            nativeBuildInputs = with pkgs; [ pkg-config ];
            buildInputs = with pkgs; [
              cargo rustc clippy rustfmt sqlite
            ] ++ pkgs.lib.optionals pkgs.stdenv.isDarwin
              (with pkgs.darwin.apple_sdk.frameworks; [ Security SystemConfiguration ]);
            shellHook = ''
              export PKG_CONFIG_PATH="${pkgs.sqlite.dev}/lib/pkgconfig:''${PKG_CONFIG_PATH:-}"
            '';
          };
        }
      );
    };
}
