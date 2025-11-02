{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.setuptools
    pkgs.python311Packages.wheel
    pkgs.postgresql_14
    pkgs.redis
    pkgs.curl
    pkgs.git
  ];
  
  env = {
    PYTHONBIN = "${pkgs.python311}/bin/python3.11";
    LANG = "en_US.UTF-8";
    PGDATA = "${toString ./.}/.postgresql";
    PGHOST = "${toString ./.}/.postgresql";
  };
}
