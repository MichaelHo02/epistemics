import json,pathlib,urllib.request,concurrent.futures,re,subprocess,hashlib
from html.parser import HTMLParser
ROOT=pathlib.Path(__file__).resolve().parent
BASE=pathlib.Path('/Users/michaelho/.local/share/openresearch/files/epistemics/track-1/global-mmlu-main')
class Text(HTMLParser):
 def __init__(self):super().__init__();self.skip=0;self.parts=[]
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.skip+=1
 def handle_endtag(self,t):
  if t in ('script','style') and self.skip:self.skip-=1
 def handle_data(self,d):
  if not self.skip:self.parts.append(d)
def fetch(u):
 k=hashlib.sha256(u.encode()).hexdigest()[:16];d=ROOT/'source-access';d.mkdir(exist_ok=True)
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 (research source verification)'}),timeout=18) as r:raw=r.read()
  if raw[:4]==b'%PDF':
   p=d/(k+'.pdf');p.write_bytes(raw);subprocess.run(['pdftotext','-layout',str(p),str(d/(k+'.txt'))],check=True,capture_output=True);s=(d/(k+'.txt')).read_text()
  else:
   p=Text();p.feed(raw.decode('utf-8','replace'));s=re.sub(r'\s+',' ',' '.join(p.parts));(d/(k+'.txt')).write_text(s)
  return {'url':u,'key':k,'characters':len(s),'status':'downloaded_requires_reading','challenge':bool(re.search(r'Checking your browser|captcha|verifying you are human',s,re.I))}
 except Exception as e:return {'url':u,'key':k,'status':'failed','error':str(e)}
if __name__=='__main__':
 rows=[json.loads(l) for l in (BASE/'selection-v2/evidence-candidates.jsonl').read_text().splitlines()];urls=sorted({r['source_url'] for r in rows if r['subject'] in ['college_biology','high_school_biology']})
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:out=list(ex.map(fetch,urls))
 (ROOT/'source-access-index.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
