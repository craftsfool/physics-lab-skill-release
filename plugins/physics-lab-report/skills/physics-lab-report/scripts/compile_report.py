#!/usr/bin/env python3
"""Export a real XeLaTeX PDF without third-party Python packages; never replace a PDF on failure."""
import argparse,json,os,shutil,subprocess,tempfile,hashlib
from pathlib import Path
from setup_environment import find_tool

def compile_report(source,output=None):
    source=Path(source).resolve()
    if not source.is_file() or source.suffix!='.tex':raise ValueError('A saved .tex source is required.')
    revision=hashlib.sha256(source.read_bytes()).hexdigest()
    engine=find_tool('xelatex')
    if not engine:raise RuntimeError('XeLaTeX missing. Offer scripts/setup_environment.py --install-latex, or use an available built-in compiler. Do not export raw math text as PDF.')
    target=Path(output).resolve() if output else source.with_suffix('.pdf')
    env=dict(os.environ);env['PATH']=str(Path(engine).parent)+os.pathsep+env.get('PATH','')
    with tempfile.TemporaryDirectory(prefix='physics-latex-build-') as tmp:
        for _ in range(2):
            r=subprocess.run([engine,'-no-shell-escape','-halt-on-error','-interaction=nonstopmode','-file-line-error','-output-directory='+tmp,str(source)],cwd=source.parent,env=env,capture_output=True,text=True,timeout=180)
            if r.returncode:raise RuntimeError('LaTeX failed; existing PDF retained. Diagnostic: '+r.stdout[-3000:])
        pdf=Path(tmp)/(source.stem+'.pdf');log=(Path(tmp)/(source.stem+'.log')).read_text(errors='replace')
        if not pdf.is_file():raise RuntimeError('Compiler produced no PDF.')
        if 'Overfull \\hbox' in log or 'Overfull \\vbox' in log:raise RuntimeError('Content overflow; adjust layout before export. Existing PDF retained.')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=revision:raise RuntimeError('Source changed during compilation; existing PDF retained. Compile the current source again.')
        target.parent.mkdir(parents=True,exist_ok=True)
        fd,staged=tempfile.mkstemp(prefix='.'+target.name+'-',dir=target.parent);os.close(fd)
        try:shutil.copy2(pdf,staged);os.replace(staged,target)
        finally:
            if os.path.exists(staged):os.unlink(staged)
    return {'success':True,'pdf':str(target),'engine':'XeLaTeX','source_sha256':revision,'visual_review_required':True}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    try:print(json.dumps(compile_report(a.source,a.output),ensure_ascii=False))
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as e:p.exit(1,str(e)+'\n')
