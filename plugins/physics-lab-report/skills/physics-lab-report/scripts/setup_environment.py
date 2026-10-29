#!/usr/bin/env python3
"""Inspect local capabilities; create empty user material folders or install TinyTeX on request."""
import argparse, importlib.util, json, os, platform, shutil, subprocess, tempfile, urllib.request
from pathlib import Path

PACKAGES = ['latexmk','ctex','fandol','pgf','pgfplots','geometry','xcolor','amsmath','enumitem','eso-pic','adjustbox','wrapfig','tools','etoolbox']

def roots(home=None, system=None):
    home=Path(home or Path.home()); system=system or platform.system()
    if system=='Windows':
        return [Path(os.environ.get('APPDATA',home/'AppData/Roaming'))/'TinyTeX/bin/windows']
    bases=[home/'Library/TinyTeX/bin',home/'.TinyTeX/bin',home/'AppData/Roaming/TinyTeX/bin']
    dirs=[Path('/Library/TeX/texbin')]
    for base in bases:
        if base.is_dir(): dirs.extend(p for p in base.iterdir() if p.is_dir())
    if Path('/usr/local/texlive').is_dir():
        dirs.extend(Path('/usr/local/texlive').glob('*/bin/*'))
    return dirs

def find_tool(name, extra=()):
    found=shutil.which(name)
    if found: return found
    suffix='.exe' if platform.system()=='Windows' else ''
    for root in [*extra,*roots()]:
        path=Path(root)/(name+suffix)
        if path.is_file() and os.access(path,os.X_OK): return str(path)
    return None

def inspect(project=None, env=None, local_materials=False):
    env=os.environ if env is None else env
    api=bool(env.get('PHYSICS_LAB_API_URL') and env.get('PHYSICS_LAB_API_TOKEN'))
    tools={name:find_tool(name) for name in ['xelatex','lualatex','tectonic','kpsewhich','tlmgr','matlab','octave','node']}
    if not tools['matlab']:
        candidates=[*Path('/Applications').glob('MATLAB*.app/bin/matlab')] if platform.system()=='Darwin' else []
        if platform.system()=='Windows': candidates=list(Path(env.get('ProgramFiles','C:/Program Files')).glob('MATLAB/R*/bin/matlab.exe'))
        if platform.system()=='Linux': candidates=list(Path('/usr/local/MATLAB').glob('R*/bin/matlab'))
        tools['matlab']=next((str(p) for p in sorted(candidates,reverse=True) if p.is_file()),None)
    modules={m:importlib.util.find_spec(m) is not None for m in ['numpy','pandas','scipy','matplotlib','openpyxl']}
    folders=[]
    if project is not None and local_materials:
        project=Path(project)
        for name in ['教材','前人智慧']:
            p=project/name; p.mkdir(parents=True,exist_ok=True); folders.append(str(p))
    config_base=Path(env.get('APPDATA',Path.home()/'AppData/Roaming')) if platform.system()=='Windows' else Path(env.get('XDG_CONFIG_HOME',Path.home()/'.config'))
    device_file=Path(env.get('PHYSICS_LAB_DEVICE_CONFIG',config_base/'physics-lab-report/device.json'))
    return {'system':platform.system(),'api_configured':api,'tools':tools,'python_modules':modules,
            'device_credential_present':device_file.is_file() and not device_file.is_symlink(),
            'local_material_folders':folders,
            'reference_mode':'local' if local_materials else ('api_configured' if api else 'awaiting_user_choice'),
            'requires_reference_choice':not api and not local_materials,
            'reference_question':('未检测到资料API配置。你希望登记设备领取30天资料 Key、配置已有API令牌，还是使用本地资料（也可不提供参考资料继续）？令牌请通过私密配置输入，不要粘贴到对话中。' if not api and not local_materials else None),
            'latex_available':bool(tools['xelatex'] or tools['lualatex'] or tools['tectonic']),
            'matlab_available':bool(tools['matlab']),
            'matlab_alternatives':['MATLAB Online: https://matlab.mathworks.com/','Python: numpy/scipy/pandas/matplotlib','Excel: formulas, scatter charts and regression','GNU Octave: check toolbox and export compatibility']}

def installation_plan(system=None):
    system=system or platform.system()
    if system in ['Darwin','Linux']:
        return {'url':'https://tinytex.yihui.org/install-bin-unix.sh','argv':['sh','<downloaded-installer>','--no-path'],
                'scope':'user_home_no_global_path_change','requires':['perl','xz'] if system=='Linux' else [],'packages':PACKAGES}
    if system=='Windows':
        return {'url':'https://tinytex.yihui.org/install-bin-windows.bat','argv':['cmd','/c','<downloaded-installer>'],
                'scope':'official_user_installer','requires':['powershell'],'packages':PACKAGES}
    raise ValueError('Unsupported OS; use the official TeX Live installer.')

def verify_latex_runtime(engine):
    source=r"""\documentclass[fontset=fandol]{ctexart}
\usepackage{tikz,pgfplots,geometry,xcolor,amsmath,enumitem,eso-pic,adjustbox,wrapfig,etoolbox}
\begin{document}环境验证：\(I=I_0\cos^2\theta,\;\frac{a}{b}\)；中文与公式。\end{document}
"""
    env=dict(os.environ);env['PATH']=str(Path(engine).parent)+os.pathsep+env.get('PATH','')
    with tempfile.TemporaryDirectory(prefix='physics-latex-smoke-') as tmp:
        p=Path(tmp)/'check.tex';p.write_text(source,encoding='utf-8')
        r=subprocess.run([engine,'-no-shell-escape','-halt-on-error','-interaction=nonstopmode',str(p)],cwd=tmp,env=env,capture_output=True,text=True,timeout=180)
        if r.returncode or not (Path(tmp)/'check.pdf').is_file():raise RuntimeError('Installed engine cannot compile Chinese/formulas/template packages. '+r.stdout[-1200:])
    return True

def install_latex():
    if find_tool('xelatex'): return {'status':'already_installed','xelatex':find_tool('xelatex')}
    plan=installation_plan()
    for name in plan['requires']:
        if not shutil.which(name): raise RuntimeError('Missing prerequisite: '+name+'. Install it before retrying.')
    with tempfile.TemporaryDirectory(prefix='physics-latex-install-') as tmp:
        p=Path(tmp)/('install.bat' if platform.system()=='Windows' else 'install.sh')
        req=urllib.request.Request(plan['url'],headers={'User-Agent':'physics-lab-report-setup'})
        with urllib.request.urlopen(req,timeout=60) as response:
            if not response.geturl().startswith('https://'): raise RuntimeError('Installer redirect must use HTTPS.')
            body=response.read(500001)
        if not body or len(body)>500000: raise RuntimeError('Unexpected installer size.')
        p.write_bytes(body)
        subprocess.run([str(p) if arg=='<downloaded-installer>' else arg for arg in plan['argv']],check=True,timeout=1800)
    engine=find_tool('xelatex'); manager=find_tool('tlmgr')
    if not engine or not manager: raise RuntimeError('Installer finished without a usable XeLaTeX/tlmgr; no success claim.')
    env=dict(os.environ);env['PATH']=str(Path(engine).parent)+os.pathsep+env.get('PATH','')
    subprocess.run([manager,'install',*PACKAGES],env=env,check=True,timeout=1200)
    subprocess.run([engine,'--version'],env=env,check=True,stdout=subprocess.DEVNULL,timeout=30)
    verify_latex_runtime(engine)
    return {'status':'installed','xelatex':engine,'packages_verified_by_install':PACKAGES,'chinese_formula_compile_verified':True}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path);p.add_argument('--local-materials',action='store_true',help='Use only after the user explicitly chooses local/no-reference mode; creates empty material folders.');p.add_argument('--install-latex',action='store_true');p.add_argument('--installation-plan',action='store_true');a=p.parse_args()
    try:
        if a.installation_plan: result=installation_plan()
        elif a.install_latex: result=install_latex()
        else: result=inspect(a.project,local_materials=a.local_materials)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValueError,RuntimeError,OSError,subprocess.SubprocessError) as e:
        p.exit(1,'Setup incomplete: '+str(e)+'\n')
if __name__=='__main__':main()
