{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.unzip
    pkgs.wget
    pkgs.git
  ];
}
