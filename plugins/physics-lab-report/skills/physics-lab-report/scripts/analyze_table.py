#!/usr/bin/env python3
"""Fit an explicitly chosen linear relation from user CSV/Excel; CSV needs only stdlib."""
import argparse,csv,json,math
from pathlib import Path

def linear_fit(x,y):
 if len(x)!=len(y) or len(x)<3:raise ValueError('At least three paired measurements are required.')
 if any(not math.isfinite(v) for v in [*x,*y]):raise ValueError('Measurements must be finite; no silent exclusions.')
 n=len(x);xm=math.fsum(x)/n;ym=math.fsum(y)/n
 sxx=math.fsum((v-xm)**2 for v in x)
 if sxx<=0:raise ValueError('Distinct x values are required.')
 slope=math.fsum((a-xm)*(b-ym) for a,b in zip(x,y))/sxx;intercept=ym-slope*xm
 fitted=[intercept+slope*v for v in x];residual=[b-f for b,f in zip(y,fitted)]
 sse=math.fsum(r*r for r in residual);sst=math.fsum((v-ym)**2 for v in y);variance=sse/(n-2)
 return {'n':n,'slope':slope,'intercept':intercept,'slope_standard_error':math.sqrt(variance/sxx),'intercept_standard_error':math.sqrt(variance*(1/n+xm*xm/sxx)),'r_squared':1-sse/sst if sst else None,'residual_std':math.sqrt(variance),'assumptions':'OLS with equal independent y variance; x uncertainty ignored. Standard errors are not total instrument uncertainty.'},fitted,residual

def read_columns(path,xcol,ycol,sheet=None):
 path=Path(path)
 if path.suffix.lower()=='.csv':
  with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
 elif path.suffix.lower()=='.xlsx':
  try:import openpyxl
  except ImportError:raise ValueError('Excel reading needs openpyxl; export CSV to use standard-library mode.')
  w=openpyxl.load_workbook(path,read_only=True,data_only=True);s=w[sheet] if sheet else w.active
  values=list(s.values);header=values[0];rows=[dict(zip(header,row)) for row in values[1:]];w.close()
 else:raise ValueError('Use UTF-8 CSV or .xlsx; legacy .xls must be exported explicitly.')
 x=[];y=[]
 for n,row in enumerate(rows,2):
  if all(v in [None,''] for v in row.values()):continue
  try:a=float(row[xcol]);b=float(row[ycol])
  except (KeyError,TypeError,ValueError):raise ValueError('Missing or nonnumeric paired value in row '+str(n)+'. For Excel, formulas must have saved numeric results.')
  x.append(a);y.append(b)
 return x,y

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--x',required=True);p.add_argument('--y',required=True);p.add_argument('--sheet');p.add_argument('--x-scale',type=float,default=1);p.add_argument('--y-scale',type=float,default=1);p.add_argument('--x-unit',default='');p.add_argument('--y-unit',default='');p.add_argument('--output',type=Path,required=True);p.add_argument('--plot',action='store_true');a=p.parse_args()
 try:
  x,y=read_columns(a.input,a.x,a.y,a.sheet);x=[v*a.x_scale for v in x];y=[v*a.y_scale for v in y];result,fit,res=linear_fit(x,y)
  if a.plot:
   try:import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
   except ImportError:raise ValueError('Plotting needs matplotlib; omit --plot to compute with standard library.')
  a.output.mkdir(parents=True,exist_ok=True);result.update(x_column=a.x,y_column=a.y,x_scale=a.x_scale,y_scale=a.y_scale,x_unit=a.x_unit,y_unit=a.y_unit,tool='Python')
  (a.output/'fit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
  with (a.output/'fit.csv').open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(['x','y','y_fit','residual']);w.writerows(zip(x,y,fit,res))
  if a.plot:
   plt.rcParams.update({'font.family':'serif','font.size':11,'axes.linewidth':1,'xtick.direction':'in','ytick.direction':'in'})
   fig,ax=plt.subplots(figsize=(6.2,4.4));ax.plot(x,y,'ks',markersize=4,label='Measured');order=sorted(range(len(x)),key=x.__getitem__);ax.plot([x[i] for i in order],[fit[i] for i in order],color='#b3282d',label='Linear fit');ax.set(xlabel=a.x+(f' ({a.x_unit})' if a.x_unit else ''),ylabel=a.y+(f' ({a.y_unit})' if a.y_unit else ''));ax.legend(frameon=False);fig.tight_layout();fig.savefig(a.output/'fit.png',dpi=300);fig.savefig(a.output/'fit.pdf');plt.close(fig)
  print(json.dumps(result,ensure_ascii=False,allow_nan=False))
 except (ValueError,OSError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
