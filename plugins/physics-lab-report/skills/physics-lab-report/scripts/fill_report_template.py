#!/usr/bin/env python3
"""Place measured LaTeX blocks on the bundled report paper; reject overflow on compilation."""
import argparse,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def escape(text):
 table={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
 return ''.join(table.get(c,c) for c in str(text))

def finite(v):
 if not isinstance(v,(int,float)) or not math.isfinite(v):raise ValueError('Expected finite number')
 return v

def create(spec,assets):
 profile=json.loads((assets/'report-space.json').read_text());styles=json.loads((assets/'report-typesetting.json').read_text());source=(assets/'blank-report.tex').read_text()
 regions={r['id']:(p['page'],r) for p in profile['pages'] for r in p['regions']}
 reserved_by_page={p['page']:p.get('reserved_areas',[]) for p in profile['pages']}
 supplied=spec.get('regions',{})
 if set(supplied)-regions.keys():raise ValueError('Unknown report region')
 if not supplied and not spec.get('continuations'):raise ValueError('No content supplied')
 pre,body=source.split(r'\begin{document}',1);body=body.rsplit(r'\end{document}',1)[0]
 pages=body.strip().split(r'\newpage')
 if len(pages)!=4:raise ValueError('Expected the four-page blank template')
 selected=spec.get('page_selection',[1,2,3,4])
 if not isinstance(selected,list) or not selected or selected!=sorted(set(selected)) or any(n not in [1,2,3,4] for n in selected):raise ValueError('Invalid page selection')
 if any(regions[rid][0] not in selected for rid in supplied):raise ValueError('Content region lies on an omitted page')
 pre += r'''
\usepackage{amsmath,amssymb,array,enumitem}
\newcommand{\LabMath}[1]{\(#1\)}
\newcommand{\LabMathUnit}[1]{\mbox{\(#1\)}}
\setlist{nosep,leftmargin=1.4em,topsep=0pt,parsep=0pt}
\newcommand{\LabMeasureField}[4]{%
 \expandafter\newsavebox\csname LabBox#1\endcsname
 \expandafter\sbox\csname LabBox#1\endcsname{\fontsize{#3}{#3}\selectfont #4}%
 \ifdim\wd\csname LabBox#1\endcsname>#2mm%
  \PackageError{lab-report}{Identity or title field #1 is too wide}%
   {Use an agreed abbreviation or adjust without covering printed labels.}%
 \fi
}
\newcommand{\LabPlaceField}[3]{%
 \node[anchor=base west,inner sep=0pt] at (#2,#3) {\expandafter\usebox\csname LabBox#1\endcsname};
}
\newcommand{\LabMeasureBlock}[6]{%
 \expandafter\newsavebox\csname LabBox#1\endcsname
 \expandafter\sbox\csname LabBox#1\endcsname{\begin{minipage}[t]{#2mm}%
  \normalfont\linespread{1}\fontsize{#4}{#5}\selectfont
  \raggedright\setlength{\parindent}{1em}\setlength{\parskip}{0pt}%
  \setlength{\mathsurround}{0pt}\relpenalty=0\binoppenalty=0%
  \thinmuskip=1.5mu\medmuskip=2mu\thickmuskip=2mu%
  \xeCJKsetup{CJKglue={\hskip 0pt},CJKecglue={\hskip .2em}}%
  \setlength{\abovedisplayskip}{2pt}\setlength{\belowdisplayskip}{2pt}%
  \setlength{\abovedisplayshortskip}{1pt}\setlength{\belowdisplayshortskip}{1pt}%
  \setlength{\tabcolsep}{2.5pt}\renewcommand{\arraystretch}{1.05}%
  #6\end{minipage}}%
 \ifdim\dimexpr\ht\csname LabBox#1\endcsname+\dp\csname LabBox#1\endcsname\relax>#3mm%
  \PackageError{lab-report}{Content block #1 exceeds its reserved height}%
   {Split or reposition this block; move supplementary content to a continuation.}%
 \fi
}
\newcommand{\LabPlaceBlock}[4]{%
 \node[anchor=north west,inner sep=0pt,#4] at (#2,#3) {\expandafter\usebox\csname LabBox#1\endcsname};
}
\newcommand{\LabPlaceRuledBlock}[6]{%
 \ifdim\dimexpr #3mm-\ht\csname LabBox#1\endcsname\relax<#4mm%
  \PackageError{lab-report}{Ruled text block #1 extends above its rectangle}%
   {Reserve sufficient room above the first baseline.}%
 \fi
 \ifdim\dimexpr #3mm+\dp\csname LabBox#1\endcsname\relax>#5mm%
  \PackageError{lab-report}{Ruled text block #1 extends below its rectangle}%
   {Enlarge the rectangle or split the content onto a continuation.}%
 \fi
 \node[anchor=base west,inner sep=0pt,#6] at (#2,#3) {\expandafter\usebox\csname LabBox#1\endcsname};
}
'''
 records=[];measurements={}
 def blocks_for(rid,data,page_no):
  if isinstance(data,str):data={'latex':data}
  _,r=regions[rid];x,y,w,h=r['rect_mm'];y+=r['header_mm'];h-=r['header_mm'];y+=.7;h-=.8
  pitch=r.get('line_pitch_mm',profile['line_pitch_mm'])
  blocks=data.get('blocks',[{'latex':data.get('latex','')}]);placed=[];out=[]
  for i,b in enumerate(blocks):
   if 'latex' not in b or not isinstance(b['latex'],str):raise ValueError('Block latex must be a string')
   default_h=h
   for area in reserved_by_page.get(page_no,[]):
    rx,ry,rw,rh=area['rect_mm'];gap=area.get('gap_mm',1)
    if x+1<rx+rw+gap and x+w-1>rx-gap and y+h>ry-gap and y<ry+rh+gap:
     default_h=min(default_h,ry-gap-y)
   rect=b.get('rect_mm',[1,0,w-2,default_h]);bx,by,bw,bh=map(finite,rect)
   if min(bx,by)<0 or min(bw,bh)<=0 or bx+bw>w+.001 or by+bh>h+.001:raise ValueError('Block outside '+rid)
   for xx,yy,ww,hh in placed:
    if bx<xx+ww-.01 and xx<bx+bw-.01 and by<yy+hh-.01 and yy<by+bh-.01:raise ValueError('Overlapping blocks in '+rid)
   for area in reserved_by_page.get(page_no,[]):
    rx,ry,rw,rh=area['rect_mm'];gap=area.get('gap_mm',1)
    if x+bx<rx+rw+gap and x+bx+bw>rx-gap and y+by<ry+rh+gap and y+by+bh>ry-gap:
     raise ValueError('Block overlaps reserved area '+area['id'])
   placed.append(rect)
   role=b.get('role','body')
   if role not in styles['roles']:raise ValueError('Unknown typesetting role')
   if role in {'body','formula'} and re.search(r'\\\[|\$\$|\\begin\{(?:align\*?|equation\*?|gather\*?|multline\*?)\}',b['latex']):
    raise ValueError('Display math breaks ruled flow; use inline equations with protected mathematical structures in body/formula blocks')
   st=styles['roles'][role];font=finite(b.get('font_pt',st['default_pt']));min_font=st['min_pt']
   if not min_font<=font<=st['max_pt']:raise ValueError('Font outside readable range for '+role)
   baseline=finite(b.get('baseline_mm',pitch if role in {'body','formula'} else st['baseline_mm']))
   if baseline<font*25.4/72.27:raise ValueError('Baseline smaller than the font em')
   label=f'p{page_no}-{rid}-{i+1}'
   measurements.setdefault(page_no,[]).append(f'\\LabMeasureBlock{{{label}}}{{{bw:.3f}}}{{{bh:.3f}}}{{{font:g}}}{{{baseline*72.27/25.4:.3f}}}{{%\n{b["latex"]}\n}}')
   background=b.get('background','white' if role in {'table','diagram'} else 'none')
   if background not in {'white','none'}:raise ValueError('Unknown block background')
   option='fill=white' if background=='white' else ''
   first_baseline=None
   if role in {'body','formula'}:
    clearance=finite(b.get('rule_clearance_mm',styles.get('math_baseline_rule_clearance_mm',1.8) if re.search(r'\\(?:[([]|t?frac|LabMath)|\$',b['latex']) else styles.get('body_baseline_rule_clearance_mm',.8)))
    if not 0<=clearance<=pitch/2:raise ValueError('Invalid rule clearance')
    rule_origin=r['rect_mm'][1]+r['header_mm']
    row=math.ceil((y+by+font*25.4/72.27+clearance-rule_origin)/pitch)
    first_baseline=rule_origin+row*pitch-clearance
    out.append(f'\\LabPlaceRuledBlock{{{label}}}{{{x+bx:.3f}}}{{{first_baseline:.3f}}}{{{y+by:.3f}}}{{{y+by+bh:.3f}}}{{{option}}}')
   else:
    out.append(f'\\LabPlaceBlock{{{label}}}{{{x+bx:.3f}}}{{{y+by:.3f}}}{{{option}}}')
   records.append({'id':label,'page':page_no,'region':rid,'role':role,'rect_mm':[round(x+bx,3),round(y+by,3),bw,bh],'font_pt':font,'baseline_mm':baseline,'background':background,'first_baseline_y_mm':round(first_baseline,3) if first_baseline is not None else None})
  return '\n'.join(out)
 def inject(pg,page_no,commands):
  needle=r'\ReportFooter{'+str(page_no)+'}'
  if needle not in pg:raise ValueError('Missing footer marker')
  pg=pg.replace(needle,commands+'\n'+needle)
  marker=r'\begin{tikzpicture}[remember picture,overlay,x=1mm,y=-1mm]'
  return pg.replace(marker,'\n'.join(measurements.get(page_no,[]))+'\n'+marker,1)
 for i in range(4):
  chunks=[]
  for rid,data in supplied.items():
   if regions[rid][0]==i+1:chunks.append(blocks_for(rid,data,i+1))
  if i<2:
   if spec.get('experiment'):
    label=f'p{i+1}-experiment'
    measurements.setdefault(i+1,[]).append(f'\\LabMeasureField{{{label}}}{{133}}{{12}}{{{escape(spec["experiment"])}}}')
    chunks.append(f'\\node[anchor=base,inner sep=0pt] at (105,67.5) {{\\expandafter\\usebox\\csname LabBox{label}\\endcsname}};')
   fields={'name':(42,46.5,22),'class':(92,46.5,22),'student_id':(121,46.5,20),'teacher':(166,46.5,23),'partner':(42,55,22),'department':(92,55,22),'major':(121,55,20),'date':(166,55,23)}
   identity=spec.get('identity',{})
   if set(identity)-fields.keys():raise ValueError('Unknown identity field')
   for key,value in identity.items():
    fx,fy,fw=fields[key]
    if value:
     label=f'p{i+1}-field-{key}';measurements.setdefault(i+1,[]).append(f'\\LabMeasureField{{{label}}}{{{fw}}}{{9.5}}{{{escape(value)}}}')
     chunks.append(f'\\LabPlaceField{{{label}}}{{{fx}}}{{{fy}}}')
  pages[i]=inject(pages[i],i+1,'\n'.join(chunks))
 pages=[pages[i-1] for i in selected]
 for extra_index,extra in enumerate(spec.get('continuations',[])):
  page_no=max(selected)+extra_index+1;rid='processing_results';g=json.loads((assets/'template-geometry.json').read_text())['pages'][2]
  heading=extra.get('heading')
  if not heading:raise ValueError('A continuation requires a scientific heading')
  pg=[r'\null',r'\begin{tikzpicture}[remember picture,overlay,x=1mm,y=-1mm]',r'\begin{scope}[shift={(current page.north west)}]']
  for j in range(g['ruled_lines']):
   ry=g['first_rule_y_mm']+j*g['pitch_mm'];pg.append(f'\\draw[line width=.22pt,dash pattern=on .55mm off .45mm] ({g["left_mm"]},{ry:.2f})--({g["right_mm"]},{ry:.2f});')
  label=f'p{page_no}-heading'
  measurements.setdefault(page_no,[]).append(f'\\LabMeasureField{{{label}}}{{172}}{{14}}{{\\sffamily\\bfseries {escape(heading)}}}')
  pg.append(f'\\LabPlaceField{{{label}}}{{19}}{{35.8}}')
  pg.append(blocks_for(rid,extra,page_no));pg.extend([r'\ReportFooter{'+str(page_no)+'}',r'\end{scope}',r'\end{tikzpicture}'])
  marker=r'\begin{tikzpicture}[remember picture,overlay,x=1mm,y=-1mm]'
  pages.append('\n'.join(pg).replace(marker,'\n'.join(measurements.get(page_no,[]))+'\n'+marker,1))
 result=pre+'\n'+r'\begin{document}'+'\n'+ ('\n'+r'\newpage'+'\n').join(pages)+'\n'+r'\end{document}'+'\n'
 return result,{'paper_mm':profile['paper_mm'],'page_count':len(pages),'blocks':records,'reserved_areas':reserved_by_page,'note':'Typeset box heights are checked by LaTeX at compilation; this manifest alone does not prove layout fit.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--content',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--assets',type=Path,default=ROOT/'assets');p.add_argument('--overwrite',action='store_true');a=p.parse_args()
 manifest=a.output.with_suffix('.layout.json')
 if not a.overwrite and (a.output.exists() or manifest.exists()):p.error('Output exists; inspect before overwrite')
 tex,meta=create(json.loads(a.content.read_text()),a.assets);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(tex);manifest.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(a.output)
if __name__=='__main__':main()
