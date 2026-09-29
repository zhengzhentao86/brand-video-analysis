#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render an agent-authored report; validate local references; package explicit files."""
import argparse,html,json,re,sys,zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit,unquote

ASSETS=Path(__file__).resolve().parents[1]/'assets'
class Inspector(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.refs=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get('id'):self.ids.append(d['id'])
        for k in ['src','poster','data-img','href']:
            if d.get(k):self.refs.append(d[k])

def local_path(root,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or any(x.startswith('.') for x in p.parts):
        raise ValueError('Unsafe bundle-relative path: '+name)
    full=(root/p).resolve()
    if root.resolve() not in full.parents:raise ValueError('Path escapes report directory: '+name)
    if not full.is_file():raise ValueError('Missing resource: '+name)
    return full

def inspect(path):
    text=path.read_text();p=Inspector();p.feed(text)
    if re.search(r'@@[A-Z_]+@@',text):raise ValueError('Unexpanded template marker')
    if len(p.ids)!=len(set(p.ids)):raise ValueError('Duplicate HTML id')
    local=set()
    for ref in p.refs:
        u=urlsplit(ref)
        if not u.scheme and not u.netloc:
            if u.path:
                name=unquote(u.path);local_path(path.parent,name);local.add(name)
            elif u.fragment and unquote(u.fragment) not in p.ids:raise ValueError('Missing anchor: '+ref)
        elif u.scheme=='file':raise ValueError('Absolute file URL in shareable report')
    return {'local_resources':sorted(local),'anchors':len(p.ids),'status':'static_checks_passed'}

def render(payload,output):
    sections=payload['sections']
    if not sections:raise ValueError('Report needs sections')
    for sec in sections:
        if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',sec['id']):raise ValueError('Invalid section id')
        if not sec['body_html'].strip():raise ValueError('Empty section')
    esc=html.escape
    nav='<strong>'+esc(payload['brand'])+' / ACTION REPORT</strong>'
    nav+=''.join('<a href="#'+x['id']+'">'+esc(x.get('nav',x['title']))+'</a>' for x in sections if x.get('show_nav',True))
    main=payload['hero_html']
    for i,x in enumerate(sections,1):
        main+=f'<section id="{x["id"]}"><div class="section-title"><span class="num">{i:02}</span><h2>{esc(x["title"])}</h2></div>'+x['body_html']+'</section>'
    values={'TITLE':esc(payload['title']),'STYLE':(ASSETS/'report.css').read_text()+'\n'+payload.get('extra_css',''),'NAV':nav,'MAIN':main,'FOOTER':esc(payload.get('footer','')),'SCRIPT':(ASSETS/'interactions.js').read_text()}
    template=(ASSETS/'report.template').read_text()
    # Single substitution prevents payload content from being interpreted as template tokens.
    rendered=re.sub(r'@@([A-Z_]+)@@',lambda m:values[m.group(1)],template)
    output.mkdir(parents=True,exist_ok=True)
    temp=output/'index.pending';temp.write_text(rendered)
    try:check=inspect(temp)
    except Exception:
        temp.unlink();raise
    temp.replace(output/'index.html')
    (output/'static-checks.json').write_text(json.dumps(check,ensure_ascii=False,indent=2))
    return check

def bundle(output,payload,zip_path):
    result=inspect(output/'index.html')
    names={'index.html','static-checks.json',*result['local_resources'],*payload.get('share_files',[])}
    forbidden={'records.json','user-correction-local.json','.env'}
    validated=[]
    for name in sorted(names):
        f=local_path(output,name)
        if f.name in forbidden or any(x in {'internal','private','history','.venv','node_modules'} for x in Path(name).parts):
            raise ValueError('Private/internal file cannot be bundled: '+name)
        validated.append((name,f))
    zip_path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
        for name,f in validated:z.write(f,'report/'+name)
    with zipfile.ZipFile(zip_path) as z:
        if z.testzip():raise ValueError('ZIP integrity check failed')
    return len(validated)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--payload',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--check-only',action='store_true');p.add_argument('--zip',type=Path)
    a=p.parse_args();payload=json.loads(a.payload.read_text()) if a.payload else {}
    if a.check_only:result=inspect(a.out/'index.html')
    else:
        if not a.payload:p.error('--payload is required to render')
        result=render(payload,a.out)
    if a.zip:result['bundle_files']=bundle(a.out,payload,a.zip)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError) as exc:print('Error: '+str(exc),file=sys.stderr);sys.exit(1)
