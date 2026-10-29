#!/usr/bin/env python3
"""Estimate handwriting capacity, retaining text that wraps around small figures/tables."""
import argparse,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def tex_escape(text):
 table={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
 return ''.join(table.get(c,c) for c in str(text))
def remaining_intervals(left,right,cuts):
 result=[(left,right)]
 for a,b in sorted(cuts):
  parts=[]
  for lo,hi in result:
   if b<=lo or a>=hi:parts.append((lo,hi))
   else:
    if lo<a:parts.append((lo,a))
    if b<hi:parts.append((b,hi))
  result=parts
 return result

def build(profile,char_width,blocks=None):
 width,height=profile['paper_mm'];pitch=profile['line_pitch_mm'];glyph_h=profile.get('char_height_mm',3.2)
 if any(not math.isfinite(v) or v<=0 for v in [width,height,pitch,char_width,glyph_h]):raise ValueError('Dimensions must be finite and positive.')
 if glyph_h>pitch:raise ValueError('Glyph height exceeds row pitch.')
 reserve=profile.get('reserve_fraction',.05)
 if not 0<=reserve<1:raise ValueError('Invalid reserve fraction.')
 ids={r['id'] for p in profile['pages'] for r in p['regions']};blocks=blocks or {}
 if set(blocks)-ids:raise ValueError('Unknown block region.')
 budget={'paper_mm':[width,height],'calibration':profile['calibration'],'line_pitch_mm':pitch,'char_width_mm':char_width,'reserve_fraction':reserve,'draft_font_pt':profile.get('draft_font_pt',9),'pages':[]}
 doc=[r'% !TEX program = xelatex',r'\documentclass[UTF8,fontset=fandol,10pt]{ctexart}',f'\\usepackage[paperwidth={width}mm,paperheight={height}mm,margin=0mm]{{geometry}}',r'\usepackage{tikz}',r'\pagestyle{empty}',r'\setlength{\parindent}{0pt}',r'\begin{document}']
 for index,page in enumerate(profile['pages']):
  row={'page':page['page'],'title':page['title'],'regions':[]}
  doc += [r'\null',r'\begin{tikzpicture}[remember picture,overlay,x=1mm,y=-1mm]',r'\begin{scope}[shift={(current page.north west)}]']
  if page.get('identity_area'):
   doc += [r'\draw[gray] (18,17) rectangle (192,62);',r'\node[anchor=north west,font=\large\bfseries] at (20,20) {'+tex_escape(page['title'])+'};',r'\node[anchor=north west,font=\small] at (20,34) {姓名、班级／学号、指导教师、同组姓名、院系／专业、实验日期};',r'\node[anchor=north west,font=\small] at (20,51) {实验名称：};']
  else:doc += [r'\node[anchor=north west,font=\large\bfseries] at (18,10) {'+tex_escape(page['title'])+'};']
  for region in page['regions']:
   region_pitch=region.get('line_pitch_mm',pitch)
   if not math.isfinite(region_pitch) or region_pitch<glyph_h:raise ValueError('Invalid region pitch.')
   x,y,w,h=region['rect_mm'];header=region.get('header_mm',10);inset=region.get('side_inset_mm',1);bottom=region.get('bottom_inset_mm',profile.get('bottom_inset_mm',1.5));offset=region.get('first_baseline_offset_mm',profile.get('first_baseline_offset_mm',4))
   if min(x,y,w,h,header,inset,bottom,offset)<0 or w<=2*inset or x+w>width or y+h>height:raise ValueError('Out-of-page region: '+region['id'])
   body_h=h-header;n=max(0,math.floor((body_h-bottom-offset)/region_pitch+1e-9)+1);chars=math.floor((w-2*inset)/char_width);objects=blocks.get(region['id'],region.get('blocks',[]))
   for obj in objects:
    bx,by,bw,bh=obj['rect_mm'];gap=obj.get('gap_mm',2)
    if any(not math.isfinite(v) for v in [bx,by,bw,bh,gap]) or min(bx,by,gap)<0 or min(bw,bh)<=0 or bx+bw>w or by+bh>body_h-bottom:raise ValueError('Invalid or overflowing block: '+region['id'])
   bands=[]
   for j in range(n):
    baseline=offset+j*region_pitch;top=max(0,baseline-glyph_h);cuts=[]
    for obj in objects:
     bx,by,bw,bh=obj['rect_mm'];gap=obj.get('gap_mm',2)
     if by<baseline+.5 and by+bh>top:cuts.append((max(inset,bx-gap),min(w-inset,bx+bw+gap)))
    for area in page.get('reserved_areas',[]):
     rx,ry,rw,rh=area['rect_mm'];gap=area.get('gap_mm',1)
     if y+header+top<ry+rh+gap and y+header+baseline+.5>ry-gap:
      cuts.append((max(inset,rx-gap-x),min(w-inset,rx+rw+gap-x)))
    spans=remaining_intervals(inset,w-inset,cuts);count=sum(math.floor((hi-lo)/char_width) for lo,hi in spans)
    bands.append({'baseline_from_body_top_mm':baseline,'spans_mm':spans,'cjk_chars_estimate':count})
   capacity=sum(b['cjk_chars_estimate'] for b in bands);recommended=math.floor(capacity*(1-reserve))
   row['regions'].append({'id':region['id'],'label':region['label'],'rect_mm':region['rect_mm'],'line_pitch_mm':region_pitch,'available_lines':n,'recommended_lines':n,'chars_per_line_estimate':chars,'text_only_chars_estimate':math.floor(n*chars*(1-reserve)),'chars_after_blocks_estimate':capacity,'recommended_chars_after_blocks':recommended,'recommended_full_line_equivalent':round(recommended/chars,2) if chars else 0,'blocks':objects,'reserved_areas':page.get('reserved_areas',[]),'line_bands':bands,'note':'近似全角字符当量；图表按实际矩形扣除并保留环绕文字；公式按真实排列另计，不机械扣整行。'})
   doc += [f'\\draw[gray] ({x},{y}) rectangle ({x+w},{y+h});',f'\\node[anchor=north west,font=\\bfseries\\small] at ({x+1},{y+1}) {{{tex_escape(region["label"])}}};']
   for band in bands:
    baseline=y+header+band['baseline_from_body_top_mm']
    for lo,hi in band['spans_mm']:doc.append(f'\\draw[dotted,gray!65] ({x+lo},{baseline}) -- ({x+hi},{baseline});')
   for obj in objects:
    bx,by,bw,bh=obj['rect_mm']
    doc += [f'\\draw[fill=gray!8] ({x+bx},{y+header+by}) rectangle ({x+bx+bw},{y+header+by+bh});',f'\\node[font=\\scriptsize,text width={max(1,bw-2)}mm,align=center] at ({x+bx+bw/2},{y+header+by+bh/2}) {{{tex_escape(obj.get("label","图表"))}\\\\{bw:g} × {bh:g} mm}};']
  if page.get('qr_reserve_mm'):
   x,y,w,h=page['qr_reserve_mm'];doc += [f'\\draw[dashed,gray] ({x},{y}) rectangle ({x+w},{y+h});',f'\\node[font=\\scriptsize,text=gray] at ({x+w/2},{y+h/2}) {{页脚避让}};']
  doc += [f'\\node[font=\\scriptsize,text=gray] at ({width/2},{height-7}) {{第{page["page"]}页 · 分区及字宽为估计，非精确套印模板}};',r'\end{scope}',r'\end{tikzpicture}']
  if index<len(profile['pages'])-1:doc.append(r'\newpage')
  budget['pages'].append(row)
 doc.append(r'\end{document}');return budget,'\n'.join(doc)+'\n'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',type=Path,default=ROOT/'assets/report-space.json');p.add_argument('--output',type=Path,required=True);p.add_argument('--char-width-mm',type=float);p.add_argument('--style',choices=['compact','regular','large'],default='regular');p.add_argument('--blocks',type=Path,help='JSON: region ID -> objects with rect_mm [x,y,w,h], relative to body top-left.');p.add_argument('--overwrite',action='store_true');a=p.parse_args()
 profile=json.loads(a.profile.read_text());profile.update(profile.get('handwriting_styles',{}).get(a.style,{}));budget,tex=build(profile,a.char_width_mm if a.char_width_mm is not None else profile.get('char_width_mm',3.0),json.loads(a.blocks.read_text()) if a.blocks else None)
 files=[a.output/'layout-budget.json',a.output/'report-space-model.tex']
 if not a.overwrite and any(f.exists() for f in files):p.error('Output exists; check before --overwrite.')
 a.output.mkdir(parents=True,exist_ok=True);files[0].write_text(json.dumps(budget,ensure_ascii=False,indent=2)+'\n');files[1].write_text(tex)
 for page in budget['pages']:
  for r in page['regions']:print(f"Page {page['page']}: {r['label']}: {r['available_lines']} lines; ~{r['chars_per_line_estimate']} chars/line; ~{r['recommended_chars_after_blocks']} chars after blocks")
if __name__=='__main__':main()
