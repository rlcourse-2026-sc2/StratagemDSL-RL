"""Patch copies of SC2 maps and read every replacement back.

Two interchangeable archive backends with the same read/add/names/close API:
  Archive           StormLib through ctypes (https://github.com/ladislav-zezula/StormLib, MIT)
  MpqEditorArchive  Ladik's MPQEditor.exe command line (Windows; wine elsewhere)
open_archive() picks one; set STRAT_MPQ_BACKEND=stormlib|mpqeditor to force it.
Objects are merged by (element tag, Id), never replaced by an empty compiler output.
"""
from __future__ import annotations
import ctypes as C
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from stratagemdsl import paths

class StormLibUnavailable(OSError):
    """The native library is missing or cannot be loaded on this system."""

class Archive:
    backend='stormlib'
    def __init__(self,library,path,readonly=True):
        library = os.environ.get("STORMLIB_PATH") or library
        if not Path(library).is_file():
            raise StormLibUnavailable(f"StormLib not found: {library}. Set STORMLIB_PATH to the native library for your OS, "
                                      "set MPQEDITOR_PATH to MPQEditor.exe, or run without --map.")
        try:
            self.lib=C.CDLL(str(library))
        except OSError as exc:
            raise StormLibUnavailable(f"cannot load StormLib {library}: {exc}. Rebuild it for this system "
                                      "with tools/build_stormlib.sh and point STORMLIB_PATH at the result, "
                                      "or set MPQEDITOR_PATH to MPQEditor.exe.") from exc
        self.h=C.c_void_p()
        spec={
          'SFileCloseArchive':([C.c_void_p],C.c_bool),
          'SFileOpenFileEx':([C.c_void_p,C.c_char_p,C.c_uint32,C.POINTER(C.c_void_p)],C.c_bool),
          'SFileGetFileSize':([C.c_void_p,C.POINTER(C.c_uint32)],C.c_uint32),
          'SFileReadFile':([C.c_void_p,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_void_p],C.c_bool),
          'SFileCloseFile':([C.c_void_p],C.c_bool),
          'SFileFlushArchive':([C.c_void_p],C.c_bool),
          'SErrGetLastError':([],C.c_uint32),
        }
        for name,(args,ret) in spec.items():
            f=getattr(self.lib,name);f.argtypes=args;f.restype=ret
        flags=0x100 if readonly else 0
        # Local file names are TCHAR: wchar_t in the bundled UNICODE Windows build,
        # char elsewhere.  A user-supplied ANSI Windows DLL is detected by retrying.
        modes=['wide','ansi'] if os.name=='nt' else ['bytes']
        for mode in modes:
            self._path_mode(mode)
            if self.lib.SFileOpenArchive(self._local(path),0,flags,C.byref(self.h)):break
        else:self.check(False,f'open archive {path}')
    def _path_mode(self,mode):
        self.mode=mode;t=C.c_wchar_p if mode=='wide' else C.c_char_p
        self.lib.SFileOpenArchive.argtypes=[t,C.c_uint32,C.c_uint32,C.POINTER(C.c_void_p)]
        self.lib.SFileOpenArchive.restype=C.c_bool
        self.lib.SFileAddFileEx.argtypes=[C.c_void_p,t,C.c_char_p,C.c_uint32,C.c_uint32,C.c_uint32]
        self.lib.SFileAddFileEx.restype=C.c_bool
    def _local(self,path):
        path=os.fspath(path)
        if self.mode=='wide':return str(path)
        if self.mode=='ansi':return str(path).encode('mbcs')
        return os.fsencode(path)
    def check(self,ok,operation):
        if not ok:raise OSError(f'{operation}: StormLib error {self.lib.SErrGetLastError()}')
    def read(self,name):
        h=C.c_void_p();self.check(self.lib.SFileOpenFileEx(self.h,name.encode(),0,C.byref(h)),f'open {name}')
        try:
            high=C.c_uint32();size=self.lib.SFileGetFileSize(h,C.byref(high))
            if high.value:raise ValueError('Map member exceeds 4 GiB')
            buf=C.create_string_buffer(size);read=C.c_uint32()
            self.check(self.lib.SFileReadFile(h,buf,size,C.byref(read),None),f'read {name}')
            if read.value!=size:raise ValueError('Short MPQ read')
            return buf.raw
        finally:self.lib.SFileCloseFile(h)
    def add(self,source,name):
        self.check(self.lib.SFileAddFileEx(self.h,self._local(source),name.encode(),0x80000000|0x200,2,2),f'write {name}')
    def names(self):return [n for n in self.read('(listfile)').decode('utf-8-sig').splitlines() if n]
    def close(self):
        if self.h:self.check(self.lib.SFileCloseArchive(self.h),'close archive');self.h=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


class MpqEditorArchive:
    """The same interface on top of MPQEditor.exe's command line.

    Reading extracts the whole archive once into a temporary folder; each add()
    is one `MPQEditor.exe add` call (command-line arguments are Unicode, so
    paths may contain Chinese).  Outside Windows the exe runs under wine.
    """
    backend='mpqeditor'
    SPECIAL={'(listfile)','(attributes)','(signature)'}
    def __init__(self,exe,path,readonly=True):
        self.exe=Path(exe);self.path=Path(path).resolve();self.readonly=readonly;self._tmp=None
        if not self.exe.is_file():raise FileNotFoundError(f'MPQEditor not found: {exe}')
        if not self.path.is_file():raise OSError(f'open archive {path}: file not found')
        self.prefix=[] if os.name=='nt' else [shutil.which('wine') or 'wine']
        self.read('(listfile)')
    def _win(self,p):
        p=str(Path(p).resolve())
        if os.name=='nt' or not shutil.which('winepath'):return p
        return subprocess.run(['winepath','-w',p],capture_output=True,text=True,encoding='utf-8',errors='replace',check=True).stdout.strip()
    def _run(self,*args,what):
        env=dict(os.environ);env.setdefault('WINEDEBUG','-all')
        # Explicit codec: on a Chinese Windows the default is GBK, and MPQEditor's output is not.
        r=subprocess.run([*self.prefix,str(self.exe),*args],capture_output=True,text=True,encoding='utf-8',errors='replace',env=env,timeout=600)
        if r.returncode!=0:raise OSError(f'{what}: MPQEditor exit code {r.returncode} {r.stdout.strip()} {r.stderr.strip()}'.strip())
    def _extracted(self):
        if self._tmp is None:
            self._tmp=tempfile.TemporaryDirectory(prefix='sc2-mpqeditor-')
            self._run('extract',self._win(self.path),'*',self._win(self._tmp.name),'/fp',what=f'extract {self.path}')
        return Path(self._tmp.name)
    def read(self,name):
        p=self._extracted().joinpath(*name.split('\\'))
        if not p.is_file():raise OSError(f'open {name}: not in archive {self.path}')
        return p.read_bytes()
    def add(self,source,name):
        if self.readonly:raise OSError(f'write {name}: archive opened read-only')
        self._run('add',self._win(self.path),self._win(source),name,'/c',what=f'write {name}')
        if self._tmp is not None:self._tmp.cleanup();self._tmp=None
    def names(self):return [n for n in self.read('(listfile)').decode('utf-8-sig').splitlines() if n]
    def close(self):
        if self._tmp is not None:self._tmp.cleanup();self._tmp=None
    def __enter__(self):return self
    def __exit__(self,*args):self.close()


def open_archive(path,readonly=True,library=None):
    """StormLib when it loads, otherwise MPQEditor.exe when one is configured.

    `library` may name either a StormLib build or MPQEditor.exe.
    """
    forced=os.environ.get('STRAT_MPQ_BACKEND','').lower()
    exe=paths.mpqeditor_path()
    if library is not None and Path(library).suffix.lower()=='.exe':forced,exe='mpqeditor',Path(library)
    if forced=='mpqeditor':
        if exe is None:raise FileNotFoundError('STRAT_MPQ_BACKEND=mpqeditor but MPQEditor.exe was not found; set MPQEDITOR_PATH')
        return MpqEditorArchive(exe,path,readonly)
    try:
        return Archive(library if library is not None else paths.stormlib_path(),path,readonly)
    except StormLibUnavailable:
        if forced=='stormlib' or exe is None:raise
        return MpqEditorArchive(exe,path,readonly)

def merge_objects(original,generated):
    base=ET.fromstring(original);extra=ET.fromstring(generated)
    if len(extra)==0:return original,0
    keys={(x.tag,x.get('Id')) for x in base}
    for x in extra:
        key=(x.tag,x.get('Id'))
        if key in keys:raise ValueError(f'Object ID collision {key}; refuse overwrite')
        base.append(x);keys.add(key)
    return ET.tostring(base,encoding='utf-8',xml_declaration=True),len(extra)

def pack_and_verify(base_map,out_map,galaxy,trigger_xml,objects_xml,library=None):
    """Copy base_map to out_map, replace MapScript/Triggers/Objects, verify by readback."""
    with open_archive(base_map,library=library) as a:
        backend=a.backend
        names=a.names();original={n:a.read(n) for n in names}
        old_objects=a.read('Objects')
    objects,added=merge_objects(old_objects,objects_xml)
    refs=set(re.findall(r'PointFromId\((\d+)\)',galaxy))
    available={x.get('Id') for x in ET.fromstring(objects).iter('ObjectPoint')}
    if refs-available:raise ValueError(f'Missing point IDs: {sorted(refs-available)}')
    payload={'MapScript.galaxy':galaxy.encode(),'Triggers':trigger_xml.encode(),'Objects':objects}
    out_map=Path(out_map);out_map.parent.mkdir(parents=True,exist_ok=True)
    # Refuse in-place edits of the original map.
    if Path(base_map).resolve()==out_map.resolve():raise ValueError('Base map must remain immutable')
    shutil.copy2(base_map,out_map)
    with tempfile.TemporaryDirectory(prefix='sc2-corpus-pack-') as tmp:
        with open_archive(out_map,False,library) as a:
            for i,(name,data) in enumerate(payload.items()):
                p=Path(tmp)/str(i);p.write_bytes(data);a.add(p,name)
    with open_archive(out_map,library=library) as a:
        for name,data in payload.items():
            if a.read(name)!=data:raise ValueError(f'Readback mismatch: {name}')
        checked=0
        for name,data in original.items():
            if name in payload or name in ['(listfile)','(attributes)','(signature)']:continue
            if a.read(name)!=data:raise ValueError(f'Unrelated map member altered: {name}')
            checked+=1
        ET.fromstring(a.read('Triggers'));ET.fromstring(a.read('Objects'))
    return {'status':'passed','backend':backend,'point_references':len(refs),'added_objects':added,'preserved_members':checked,'objects_preserved_exactly':objects==old_objects,'replaced_members':list(payload),'map_sha256':hashlib.sha256(out_map.read_bytes()).hexdigest(),'bytes':out_map.stat().st_size}
