#!/usr/bin/env bash
# Build StormLib from source.
#
#   tools/build_stormlib.sh [OUT_DIR]             # Linux: OUT_DIR/libstorm.so
#   tools/build_stormlib.sh --windows [OUT_DIR]   # cross-compile OUT_DIR/StormLib.dll (needs mingw-w64)
#
# OUT_DIR defaults to assets/native.  zlib/bzip2/libtomcrypt are compiled in
# from StormLib's own copies.  On Linux, tools/native/glibc_compat.c pins
# fstat64 and strtoul to the old glibc ABI so the result loads on glibc 2.14+.
# The Windows DLL is the UNICODE build with the MinGW runtime linked
# statically, so it needs only DLLs that ship with Windows.
set -euo pipefail

TARGET=linux
if [[ "${1:-}" == "--windows" ]]; then TARGET=windows; shift; fi
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="${1:-$REPO/assets/native}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

git clone -q --depth 1 https://github.com/ladislav-zezula/StormLib.git "$WORK/StormLib"
COMMON=(-DBUILD_SHARED_LIBS=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON -DCMAKE_BUILD_TYPE=Release)

if [[ $TARGET == linux ]]; then
  gcc -O2 -fPIC -c "$REPO/tools/native/glibc_compat.c" -o "$WORK/glibc_compat.o"
  cmake -S "$WORK/StormLib" -B "$WORK/build" "${COMMON[@]}" \
    -DCMAKE_SHARED_LINKER_FLAGS="$WORK/glibc_compat.o" >/dev/null
else
  CC=x86_64-w64-mingw32-gcc-posix; CXX=x86_64-w64-mingw32-g++-posix
  command -v $CXX >/dev/null || CXX=x86_64-w64-mingw32-g++ CC=x86_64-w64-mingw32-gcc
  cat > "$WORK/mingw.cmake" <<CMAKE
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER $CC)
set(CMAKE_CXX_COMPILER $CXX)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
CMAKE
  cmake -S "$WORK/StormLib" -B "$WORK/build" "${COMMON[@]}" -DSTORM_UNICODE=ON \
    -DCMAKE_TOOLCHAIN_FILE="$WORK/mingw.cmake" \
    -DCMAKE_SHARED_LINKER_FLAGS="-static -static-libgcc -static-libstdc++" >/dev/null
fi
cmake --build "$WORK/build" -j"$(nproc)" >"$WORK/build.log" 2>&1 || { tail -30 "$WORK/build.log"; exit 1; }

mkdir -p "$OUT_DIR"
if [[ $TARGET == linux ]]; then
  install -m 755 "$(readlink -f "$WORK/build/libstorm.so")" "$OUT_DIR/libstorm.so"
  strip --strip-unneeded "$OUT_DIR/libstorm.so"
  echo "built $OUT_DIR/libstorm.so; newest glibc symbol required:"
  readelf --dyn-syms -W "$OUT_DIR/libstorm.so" | grep -oE 'GLIBC_[0-9.]+' | sort -V | tail -1
else
  install -m 755 "$WORK"/build/*StormLib.dll "$OUT_DIR/StormLib.dll"
  x86_64-w64-mingw32-strip --strip-unneeded "$OUT_DIR/StormLib.dll"
  echo "built $OUT_DIR/StormLib.dll; imports:"
  x86_64-w64-mingw32-objdump -p "$OUT_DIR/StormLib.dll" | grep "DLL Name"
fi
