"""Public web snapshots are evidence bytes, never model instructions or automatic facts."""
import urllib.request,urllib.parse,socket,ipaddress,re,hashlib,json,uuid,http.client,ssl,xml.etree.ElementTree as ET
from html.parser import HTMLParser
from vnext.providers.settings import NoRedirect
from vnext.contracts import utc_now
from vnext.phase2.knowledge import Knowledge
class Text(HTMLParser):
    def __init__(self):super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style','noscript'):self.skip+=1
        if t in ('p','div','br','h1','h2','li'):self.parts.append('\n')
    def handle_endtag(self,t):
        if t in ('script','style','noscript'):self.skip=max(0,self.skip-1)
    def handle_data(self,d):
        if not self.skip:self.parts.append(d)

def public_addresses(value):
    s=urllib.parse.urlsplit(value)
    if s.scheme!='https' or not s.hostname or s.username or s.password:raise ValueError('PUBLIC_HTTPS_SOURCE_REQUIRED')
    if s.port not in (None,443):raise ValueError('SOURCE_PORT_FORBIDDEN')
    addresses=socket.getaddrinfo(s.hostname,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise ValueError('PRIVATE_SOURCE_ADDRESS_FORBIDDEN')
    return s,list(dict.fromkeys(a[4][0] for a in addresses))

def public_url(value):
    public_addresses(value)
    return value

class PinnedHTTPS(http.client.HTTPSConnection):
    """Connect to an already checked public IP, verifying TLS against the original host."""
    def __init__(self,host,address,timeout=25):
        super().__init__(host,port=443,timeout=timeout,context=ssl.create_default_context());self.address=address
    def connect(self):
        sock=socket.create_connection((self.address,443),self.timeout)
        try:self.sock=self._context.wrap_socket(sock,server_hostname=self.host)
        except Exception:sock.close();raise

def fetch(value):
    parsed,addresses=public_addresses(value)
    target=parsed.path or '/'
    if parsed.query:target+='?'+parsed.query
    conn=PinnedHTTPS(parsed.hostname,addresses[0])
    try:
        conn.request('GET',target,headers={'User-Agent':'ContentOS/0.2.1 EvidenceSnapshot'})
        r=conn.getresponse()
        if not 200<=r.status<300:raise ValueError('SOURCE_HTTP_'+str(r.status))
        raw=r.read(2_000_001);mime=r.headers.get('Content-Type','');charset=r.headers.get_content_charset() or 'utf-8'
    finally:conn.close()
    if len(raw)>2_000_000:raise ValueError('SOURCE_TOO_LARGE')
    if not any(x in mime for x in ('text/','json','xml')):raise ValueError('SOURCE_FORMAT_UNSUPPORTED')
    html=raw.decode(charset,errors='replace');parser=Text();parser.feed(html)
    text=''.join(parser.parts).strip() if 'html' in mime else html
    if not text:raise ValueError('SOURCE_EMPTY')
    return {'text':text,'raw':raw,'url':value,'mime':mime,'snapshot':hashlib.sha256(raw).hexdigest()}

def search(query):
    url='https://www.bing.com/search?format=rss&q='+urllib.parse.quote(query)
    result=fetch(url)
    try:
        tree=ET.fromstring(result['raw']);items=[{'title':i.findtext('title'),'url':i.findtext('link'),'snippet':i.findtext('description')} for i in tree.findall('.//item')]
    except ET.ParseError:raise ValueError('SEARCH_RESPONSE_UNRECOGNIZED') from None
    return {'results':items[:5],'provenance':{'adapter':'BING_PUBLIC_RSS_V1','query':query,'retrieved_at':utc_now(),'url':url},'automatic_fact':False}

def snapshot(store,pid,url):
    value=fetch(url);sid='WEB-'+uuid.uuid4().hex[:10];folder=store.root/'projects'/pid/'research/snapshots';folder.mkdir(parents=True,exist_ok=True)
    (folder/(value['snapshot']+'.snapshot')).write_bytes(value['raw'])
    source=Knowledge(store).source(pid,{'source_id':sid,'source_type':'WEB','title':url,'url':url,'retrieved_at':utc_now(),'content':value['text'],'excerpt':value['text'][:2000],'snapshot':value['snapshot'],'trust':'UNTRUSTED_SOURCE_DATA'},'RESEARCH')
    return source
