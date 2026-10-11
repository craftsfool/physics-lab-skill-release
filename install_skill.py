#!/usr/bin/env python3
"""Install a checksum-verified private release; never overwrite an existing skill."""
import argparse,hashlib,json,re,shutil,stat,zipfile
from pathlib import Path,PurePosixPath
MAX_BYTES=20_000_000
NAME='physics-lab-report'
def install(archive,checksum_file,destination):
 checksum=checksum_file.read_text().split()[0]
 if not re.fullmatch('[0-9a-fA-F]{64}',checksum):raise ValueError('Invalid release checksum.')
 if archive.stat().st_size>MAX_BYTES:raise ValueError('Archive too large.')
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=checksum.lower():raise ValueError('Release checksum mismatch.')
 payload={}
 with zipfile.ZipFile(archive) as z:
  if sum(i.file_size for i in z.infolist())>MAX_BYTES:raise ValueError('Unpacked release too large.')
  for i in z.infolist():
   p=PurePosixPath(i.filename);mode=i.external_attr>>16
   if i.filename in payload or p.is_absolute() or '..' in p.parts or not p.parts or p.parts[0]!=NAME or i.is_dir() or '\\' in i.filename or stat.S_ISLNK(mode):raise ValueError('Unsafe archive entry.')
   payload[i.filename]=z.read(i)
 manifest_name=NAME+'/manifest.json'
 if manifest_name not in payload:raise ValueError('Missing package manifest.')
 manifest=json.loads(payload.pop(manifest_name));files=manifest.get('files')
 if not isinstance(files,dict) or set(files)!=set(payload):raise ValueError('Manifest file mismatch.')
 for name,data in payload.items():
  if files[name]!=hashlib.sha256(data).hexdigest():raise ValueError('Package file checksum mismatch.')
 if NAME+'/SKILL.md' not in payload:raise ValueError('Missing skill entrypoint.')
 destination.mkdir(parents=True,exist_ok=True);target=destination/NAME
 target.mkdir()  # exclusive: FileExistsError also rejects a symlink
 try:
  for name,data in payload.items():
   p=target/Path(*PurePosixPath(name).parts[1:]);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 except BaseException:
  shutil.rmtree(target);raise
 return target
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--sha256-file',type=Path,required=True);p.add_argument('--destination',type=Path,default=Path.home()/'.codex/skills');a=p.parse_args()
 try:print(install(a.archive,a.sha256_file,a.destination))
 except (ValueError,OSError,zipfile.BadZipFile) as e:p.exit(1,'Installation failed: '+str(e)+'\n')
