{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
			let
				pkgs = nixpkgs.legacyPackages.${system};
				deps = with pkgs; [
					libspatialite
				];
			in
			{
				devShell = pkgs.mkShell {
					packages = deps ++ (with pkgs; [
					]);
				};
			}
		);
}
