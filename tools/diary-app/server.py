"""Local workbook-backed diary. No cloud upload. Loopback HTTP only."""
import argparse,datetime,hashlib,json,os,secrets,shutil,tempfile,threading,webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import openpyxl
from openpyxl.workbook.properties import CalcProperties
ROOT=Path(__file__).resolve().parent
HEADERS=['날짜','현장명','담당자','협의 항목','협의 내용','결정 사항','조치 사항','특이 사항','결정할 사항','전달할 사항','캘린더에 들어갈 사항']
def text(v):
 if isinstance(v,(datetime.date,datetime.datetime)):return v.strftime('%Y-%m-%d')
 return '' if v is None else str(v)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def expanded(ws):
 merged={}
 for m in ws.merged_cells.ranges:
  root=ws.cell(m.min_row,m.min_col)
  for row in ws.iter_rows(min_row=m.min_row,max_row=m.max_row,min_col=m.min_col,max_col=m.max_col):
   for c in row:merged[(c.row,c.column)]=(root.row,root.column)
 return merged
class Store:
 def __init__(self,path):self.path=Path(path).resolve();self.lock=threading.RLock();self.cache=None;self.stamp=None
 def snapshot(self):
  with self.lock:
   stamp=self.path.stat().st_mtime_ns,self.path.stat().st_size
   if self.cache is not None and self.stamp==stamp:return self.cache
   wb=openpyxl.load_workbook(self.path,data_only=False)
   result={'file':self.path.name,'path':str(self.path),'revision':digest(self.path),'sheets':[],'defaultSheet':'M2611' if 'M2611' in wb.sheetnames else wb.sheetnames[0]}
   for ws in wb:
    headers=[text(ws.cell(1,c).value) for c in range(1,min(ws.max_column,30)+1)]
    standard=headers[:11]==HEADERS;merges=expanded(ws) if standard else {}
    rows=[]
    for ri in range(2,ws.max_row+1):
     vals=[];roots=[]
     for ci in range(1,12 if standard else min(ws.max_column,30)+1):
      root=merges.get((ri,ci),(ri,ci));vals.append(text(ws.cell(*root).value));roots.append(ws.cell(*root).coordinate)
     if standard:
      if not (ws.cell(ri,4).value or ws.cell(ri,5).value):continue
     elif not any(vals):continue
     rows.append({'row':ri,'values':vals,'roots':roots})
    result['sheets'].append({'name':ws.title,'standard':standard,'headers':HEADERS if standard else headers,'rows':rows})
   wb.close();self.cache=result;self.stamp=stamp;return result
 def update(self,sheet,row,column,value,revision):
  with self.lock:
   if digest(self.path)!=revision:raise Conflict('엑셀이 다른 곳에서 변경되었습니다. 다시 불러온 뒤 수정 내용을 확인해 주세요.')
   if not isinstance(value,str) or len(value)>32767:raise ValueError('셀 내용은 32,767자 이하로 입력해 주세요.')
   if type(row)is not int or type(column)is not int or row<2 or column<0 or column>10:raise ValueError('수정 위치가 올바르지 않습니다.')
   snapshot=self.snapshot();info=next((s for s in snapshot['sheets'] if s['name']==sheet),None)
   if not info or not info['standard'] or not any(r['row']==row for r in info['rows']):raise ValueError('수정할 업무일지 행을 찾지 못했습니다.')
   wb=openpyxl.load_workbook(self.path);ws=wb[sheet];merged=expanded(ws);rr,cc=merged.get((row,column+1),(row,column+1));cell=ws.cell(rr,cc)
   before=text(cell.value)
   if before==value:wb.close();return {'changed':False,'cell':cell.coordinate}
   backupdir=self.path.parent/'업무일지_백업';backupdir.mkdir(exist_ok=True)
   stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');backup=backupdir/(self.path.stem+'_'+stamp+'.xlsx')
   shutil.copy2(self.path,backup)
   affected=sum(1 for r in info['rows'] if r['roots'][column]==cell.coordinate)
   coordinate=cell.coordinate
   if column==0 and value:
    try:cell.value=datetime.datetime.strptime(value,'%Y-%m-%d')
    except ValueError:wb.close();raise ValueError('날짜는 YYYY-MM-DD 형식으로 입력해 주세요.')
   else:cell.value=value;cell.data_type='s'
   wb.calculation=CalcProperties(fullCalcOnLoad=True)
   tmp=None
   try:
    fd,tmp=tempfile.mkstemp(prefix='.km-save-',suffix='.xlsx',dir=self.path.parent);os.close(fd);wb.save(tmp);wb.close()
    check=openpyxl.load_workbook(tmp,read_only=True);check.close()
    if digest(self.path)!=revision:raise Conflict('저장 중 원본 파일이 다른 곳에서 변경됐습니다. 덮어쓰지 않았습니다.')
    os.replace(tmp,self.path);tmp=None
   except PermissionError:raise ValueError('엑셀 파일이 열려 있거나 쓰기 권한이 없습니다. Excel에서 닫고 다시 저장해 주세요.')
   finally:
    wb.close()
    if tmp and Path(tmp).exists():Path(tmp).unlink()
   event={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sheet':sheet,'row':row,'cell':coordinate,'before':before,'after':value,'affectedRows':affected,'backup':str(backup)}
   logerror=None
   try:
    with (backupdir/'수정이력.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event,ensure_ascii=False)+'\n')
   except OSError:logerror='엑셀 저장과 백업은 완료됐지만 수정이력 파일을 쓰지 못했습니다.'
   self.cache=None;self.stamp=None
   return {'changed':True,'cell':coordinate,'affectedRows':affected,'backup':backup.name,'warning':logerror}
class Conflict(Exception):pass

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workbook',default=str(ROOT/'data'/'업무일지_작업용.xlsx'));ap.add_argument('--port',type=int,default=8790);ap.add_argument('--no-browser',action='store_true');ap.add_argument('--choose',action='store_true');args=ap.parse_args()
 if args.choose:
  import tkinter as tk
  from tkinter import filedialog
  root=tk.Tk();root.withdraw()
  selected=filedialog.askopenfilename(title='사용할 업무일지 선택 — 수정 시 백업 후 이 파일에 저장',filetypes=[('Excel 업무일지','*.xlsx')],initialfile='1.업무일지.xlsx')
  root.destroy()
  if not selected:return
  args.workbook=selected
 store=Store(args.workbook);store.snapshot();token=secrets.token_urlsafe(32)
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def send(self,code,obj,ctype='application/json; charset=utf-8'):
   raw=json.dumps(obj,ensure_ascii=False).encode() if isinstance(obj,(dict,list)) else obj
   self.send_response(code);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
  def authorized(self):return self.headers.get('X-KM-Token')==token
  def allowed_host(self):return self.headers.get('Host','') in ('127.0.0.1:'+str(args.port),'localhost:'+str(args.port))
  def do_GET(self):
   if not self.allowed_host():self.send(403,{'error':'로컬 주소에서만 접근할 수 있습니다.'});return
   if self.path=='/':self.send(200,(ROOT/'index.html').read_text().replace('__TOKEN__',token).encode(),'text/html; charset=utf-8');return
   if not self.authorized():self.send(403,{'error':'접근 권한이 없습니다.'});return
   try:
    if self.path=='/api/data':self.send(200,store.snapshot())
    elif self.path=='/api/download':self.send(200,store.path.read_bytes(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:self.send(404,{'error':'주소가 없습니다.'})
   except Exception as e:self.send(500,{'error':str(e)})
  def do_POST(self):
   if not self.allowed_host():self.send(403,{'error':'로컬 주소에서만 접근할 수 있습니다.'});return
   if not self.authorized():self.send(403,{'error':'접근 권한이 없습니다.'});return
   if self.path!='/api/edit':self.send(404,{'error':'주소가 없습니다.'});return
   try:
    length=int(self.headers.get('Content-Length','0'))
    if length<1 or length>300000:raise ValueError('요청 크기가 올바르지 않습니다.')
    body=json.loads(self.rfile.read(length));result=store.update(body['sheet'],body['row'],body['column'],body['value'],body['revision']);self.send(200,result)
   except Conflict as e:self.send(409,{'error':str(e)})
   except (ValueError,KeyError,TypeError) as e:self.send(400,{'error':str(e)})
   except Exception as e:self.send(500,{'error':str(e)})
 server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
 print('연결 파일:',store.path);print('실행 주소: http://127.0.0.1:'+str(args.port));print('종료: 이 창에서 Ctrl+C')
 if not args.no_browser:threading.Timer(.5,lambda:webbrowser.open('http://127.0.0.1:'+str(args.port))).start()
 try:server.serve_forever()
 except KeyboardInterrupt:pass
 finally:server.server_close()
if __name__=='__main__':main()
