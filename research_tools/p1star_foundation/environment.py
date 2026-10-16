"""Read-only identity checks for the isolated exact-arithmetic runtime."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import sysconfig


def file_identity(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    size = 0
    with path.open('rb') as stream:
        while chunk := stream.read(1024**2):
            size += len(chunk)
            digest.update(chunk)
    return {'path':str(path),'bytes':size,'sha256':digest.hexdigest()}


def loaded_z3_library():
    # Generated z3core.py discards its CDLL handle name after binding. Read the
    # actually mapped library rather than guessing from a package directory.
    import z3
    z3.get_full_version()
    paths = set()
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields = line.split(maxsplit=5)
        if len(fields) == 6 and Path(fields[5]).name == 'libz3.so':
            paths.add(fields[5])
    if len(paths) != 1:
        raise RuntimeError('cannot identify one mapped Z3 library')
    return file_identity(paths.pop())


def collect_runtime():
    import z3
    packages = []
    for name in ('z3-solver','sympy','mpmath'):
        dist = importlib.metadata.distribution(name)
        records = []
        for member in sorted(dist.files or (),key=str):
            # pyc caches are interpreter-generated; RECORD itself is separately
            # fingerprinted. No compiled cache is treated as original source.
            if str(member).endswith('.pyc'):
                continue
            path = dist.locate_file(member)
            if path.is_file():
                row = file_identity(path)
                records.append([str(member),row['bytes'],row['sha256']])
        data = json.dumps(records,separators=(',',':')).encode()
        metadata = Path(dist._path)/'METADATA'
        packages.append({'name':name,'version':dist.version,
                         'METADATA':file_identity(metadata),'installed_file_count':len(records),
                         'installed_file_manifest_sha256':hashlib.sha256(data).hexdigest()})
    libpython = Path(sysconfig.get_config_var('LIBDIR'))/sysconfig.get_config_var('LDLIBRARY')
    binary = Path(sys.prefix)/'bin/z3'
    return {'python_version':platform.python_version(),'python_binary':file_identity(sys.executable),
            'libpython':file_identity(libpython),'platform':platform.platform(),
            'runtime_packages':packages,'z3_full_version':z3.get_full_version(),
            'z3_mapped_library':loaded_z3_library(),'z3_executable':file_identity(binary),
            'isolation':{'prefix':sys.prefix,'base_prefix':sys.base_prefix,
                         'system_site_packages':False},
            'scope':'identity snapshot; no P1* input or feasibility computation'}


def require_bound_backend(lock_path=None):
    import z3
    path = Path(lock_path) if lock_path else Path(__file__).with_name('environment_lock.json')
    lock = json.loads(path.read_text())
    if z3.get_full_version() != lock['runtime']['z3_full_version']:
        raise RuntimeError('backend version differs from frozen environment')
    actual = loaded_z3_library()
    expected = lock['runtime']['z3_mapped_library']
    if actual['bytes'] != expected['bytes'] or actual['sha256'] != expected['sha256']:
        raise RuntimeError('mapped Z3 library differs from frozen environment')
    for name in ('z3-solver','sympy','mpmath'):
        expected_version = next(p['version'] for p in lock['runtime']['runtime_packages'] if p['name']==name)
        if importlib.metadata.version(name) != expected_version:
            raise RuntimeError('runtime package version differs: '+name)


if __name__ == '__main__':
    require_bound_backend()
    print(json.dumps({'bound_backend_identity':'PASS','runtime':collect_runtime()},indent=2))
