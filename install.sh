#!/usr/bin/env bash
# Install longrun and set up the kit in the current git repo.
#   curl -fsSL https://raw.githubusercontent.com/Himanshu-Sangshetti/cursor-longrun/main/install.sh | bash -s -- --preset code
#   or, from a checkout:  ./install.sh --preset code
# Arguments are passed to `longrun init`. Set LONGRUN_NO_INIT=1 to only install.
# Installs to ~/.local/share/cursor-longrun and links ~/.local/bin/longrun.
set -eu
REPO=${LONGRUN_REPO:-Himanshu-Sangshetti/cursor-longrun}
REF=${LONGRUN_REF:-main}
SHARE=${LONGRUN_SHARE:-$HOME/.local/share/cursor-longrun}
BIN=${LONGRUN_BIN:-$HOME/.local/bin}

src=""
case "${BASH_SOURCE[0]:-}" in
  */install.sh|install.sh) d=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd); [ -x "$d/bin/longrun" ] && [ -d "$d/kit" ] && src=$d ;;
esac

if [ -n "$src" ]; then
  home=$src
  echo "longrun: using the checkout at $home"
else
  command -v curl >/dev/null || { echo "install: curl is required" >&2; exit 1; }
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL "https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF" | tar -xz -C "$tmp"
  rm -rf "$SHARE"; mkdir -p "$(dirname "$SHARE")"
  mv "$tmp"/*/ "$SHARE"
  home=$SHARE
  echo "longrun: installed to $home"
fi

mkdir -p "$BIN"
ln -sf "$home/bin/longrun" "$BIN/longrun"
echo "longrun: linked $BIN/longrun"
case ":$PATH:" in *":$BIN:"*) ;; *) echo "longrun: add $BIN to your PATH, e.g. echo 'export PATH=\"$BIN:\$PATH\"' >> ~/.zshrc" ;; esac

if [ "${LONGRUN_NO_INIT:-}" = 1 ]; then exit 0; fi
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  "$home/bin/longrun" init "$@"
else
  echo "longrun: not in a git repo, so skipped init. Run 'longrun init --preset code' inside your project."
fi
