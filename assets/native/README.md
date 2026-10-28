# StormLib

[StormLib](https://github.com/ladislav-zezula/StormLib)（MIT，见 `StormLib-LICENSE`）供 `stratagemdsl.packaging` 读写 `.SC2Map`（MPQ）文件。`stratagemdsl.paths.stormlib_path()` 按系统选择：

| 文件 | 系统 | 依赖 |
| --- | --- | --- |
| `libstorm.so` | Linux x86-64 / WSL | `libc`（glibc 2.14+）、`libstdc++`、`libgcc_s`；Ubuntu 16.04+、CentOS 7+ |
| `StormLib.dll` | Windows x64（64 位 Python） | 只依赖系统自带的 `KERNEL32`、`msvcrt`、`USER32`、`WININET`；UNICODE 版，路径可含中文 |

两者都内置 zlib / bzip2 / libtomcrypt。环境变量 `STORMLIB_PATH` 可指向其他构建（例如 macOS 的 `libstorm.dylib`、32 位 Python 用的 DLL）；Windows 上自备的 ANSI 版 DLL 也能用，会自动识别。不需要地图打包时不必提供它：`strat compile` 及以下各层都不加载原生库。

## 备选：MPQEditor.exe

StormLib 库在你的系统上加载不了时，可以改用 Ladik 的 [MPQ Editor](http://www.zezula.net/en/mpq/download.html)（`MPQEditor.exe`，免费软件，不随仓库提供）。放到 `assets/native/MPQEditor.exe`，或用 `MPQEDITOR_PATH` 指向它：

```powershell
$env:MPQEDITOR_PATH = "D:\tools\MPQEditor.exe"
strat mapinfo assets\base_maps\cerulean_fall_le.SC2Map
```

选择规则：StormLib 能加载就用 StormLib，否则自动改用 MPQEditor.exe；`STRAT_MPQ_BACKEND=stormlib` 或 `mpqeditor` 可强制指定。MPQEditor 方式通过命令行 `MPQEditor.exe extract … /fp` 和 `MPQEditor.exe add … /c` 读写地图，结果仍逐项读回校验；`result.json` 的 `map.backend` 会记下用了哪种。它每次读写都要启动一次 exe，比 StormLib 慢一些。Linux 上装了 wine 也能用它（主要用于测试）。

## 重建 StormLib


```bash
tools/build_stormlib.sh                 # Linux 版，需要 git、cmake、gcc/g++
tools/build_stormlib.sh --windows       # 在 Linux 上交叉编译 Windows 版，需要 mingw-w64
```

在 Windows 上用 Visual Studio 自己编译时：

```powershell
git clone https://github.com/ladislav-zezula/StormLib
cmake -S StormLib -B build -A x64 -DBUILD_SHARED_LIBS=ON -DSTORM_UNICODE=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON
cmake --build build --config Release
$env:STORMLIB_PATH = "$PWD\build\Release\StormLib.dll"
```

`tools/native/glibc_compat.c` 把 `fstat64`、`strtoul` 绑定到旧版 glibc 接口，所以在新系统上编译出的 Linux 库也能在旧系统上加载。
