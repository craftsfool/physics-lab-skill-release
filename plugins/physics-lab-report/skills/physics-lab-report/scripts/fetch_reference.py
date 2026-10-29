#!/usr/bin/env python3
"""Fetch one authorized reference module; standard library only."""
import argparse, json, os, re, sys, subprocess, shutil
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError

TOPICS = {'purpose','theory','instruments','procedure','data_processing','uncertainty','questions','discussion'}
MAX_BYTES = 16000
class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def endpoint(value):
    p=urlsplit(value)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment or p.path!='/api/reference':
        raise ValueError('Use an HTTPS endpoint ending in /api/reference without credentials, query or fragment.')
    return value

def fetch(url, token, experiment, library, topic, opener=None, protection_bypass=None):
    endpoint(url)
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,47}',experiment) or library not in {'textbook','senior'} or topic not in TOPICS:
        raise ValueError('Invalid experiment, library or topic.')
    if not re.fullmatch(r'plr_[A-Za-z0-9_-]{43}',token):
        raise ValueError('Missing or invalid API credential.')
    body=json.dumps(dict(experiment=experiment,library=library,topic=topic)).encode()
    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','Accept':'application/json'}
    if protection_bypass:
        if not re.fullmatch(r'[A-Za-z0-9_-]{16,256}',protection_bypass):
            raise ValueError('Invalid deployment access configuration.')
        headers['x-vercel-protection-bypass']=protection_bypass
    req=Request(url,data=body,headers=headers,method='POST')
    try:
        with (opener or build_opener(NoRedirect())).open(req,timeout=20) as response:
            if response.headers.get_content_type()!='application/json': raise ValueError('Invalid response type.')
            raw=response.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES: raise ValueError('Response exceeds client limit.')
    except HTTPError as error:
        raise ValueError('Reference API returned HTTP '+str(error.code)+'.') from None
    except (URLError,TimeoutError):
        raise ValueError('Reference API unavailable.') from None
    data=json.loads(raw)
    allowed={'schema_version','experiment','library','topic','version','summary','key_points','formulas','figures','sources','retrieved_at'}
    if not isinstance(data,dict) or set(data)!=allowed or data['schema_version']!=1 or data['experiment']!=experiment or data['library']!=library or data['topic']!=topic:
        raise ValueError('Response schema or module mismatch.')
    return data

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--experiment',required=True);p.add_argument('--library',choices=['textbook','senior'],required=True)
    p.add_argument('--topic',choices=sorted(TOPICS),required=True)
    p.add_argument('--device',action='store_true',help='Use the locally registered device key; requires Node.js.')
    args=p.parse_args()
    try:
        if args.device:
            node=shutil.which('node')
            if not node:raise ValueError('Device access requires an existing Node.js runtime.')
            result=subprocess.run([node,str(Path(__file__).with_name('device_client.mjs')),'fetch','--experiment',args.experiment,'--library',args.library,'--topic',args.topic],capture_output=True,text=True,timeout=50)
            if result.returncode:raise ValueError('Device reference access failed; check device status, expiry and network.')
            sys.stdout.write(result.stdout)
            return 0
        data=fetch(os.environ.get('PHYSICS_LAB_API_URL',''),os.environ.get('PHYSICS_LAB_API_TOKEN',''),args.experiment,args.library,args.topic,protection_bypass=os.environ.get('PHYSICS_LAB_DEPLOYMENT_BYPASS'))
        sys.stdout.write(json.dumps(data,ensure_ascii=False)+'\n')
    except (ValueError,OSError,json.JSONDecodeError,subprocess.SubprocessError) as error:
        # Only controlled validation errors reach the terminal; never HTTP bodies or credentials.
        print(str(error) if isinstance(error,ValueError) and not isinstance(error,json.JSONDecodeError) else 'Could not parse reference module.',file=sys.stderr)
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
