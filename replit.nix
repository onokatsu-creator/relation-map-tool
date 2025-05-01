{ pkgs }: {
  deps = [
    pkgs.python310
    pkgs.python310Packages.pip
    pkgs.cairo
    pkgs.ffmpeg-full
    pkgs.fontconfig
    pkgs.freetype
    pkgs.glib
    pkgs.ghostscript
    pkgs.pango
    pkgs.ipaexfont  # IPAGothicフォントパッケージ
  ];
}
