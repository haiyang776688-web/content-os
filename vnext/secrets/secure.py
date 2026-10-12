"""macOS Keychain only for persistent credentials. Fail closed on other backends."""
import os,re,sys,json,logging
KNOWN=set()
def remember(value):
    if value and len(value)>=12:KNOWN.add(value)
    return value

def redact(value):
    if isinstance(value,dict):
        safe={'secret_configured','secret_source','credentials_available','cached_tokens','input_tokens','output_tokens','max_tokens','max_output_tokens','total_tokens','usage_tokens','csrf_token'}
        return {k:('[REDACTED]' if k.lower() not in safe and re.search(r'(?i)^(authorization|api.?key|credentials?|(?:access|refresh|id)[_-]token|(?:x[-_])?api[-_]?key|secret|secret_header|password|token)$',k) else redact(v)) for k,v in value.items()}
    if isinstance(value,list):return [redact(x) for x in value]
    if not isinstance(value,str):return value
    for secret in sorted(KNOWN,key=len,reverse=True):value=value.replace(secret,'[REDACTED]')
    value=re.sub(r'(?i)(Bearer\s+)[^\s"\'\\]+',r'\1[REDACTED]',value)
    value=re.sub(r'(?i)(?<![A-Za-z0-9_])(sk[-_][A-Za-z0-9_-]{10,})','[REDACTED]',value)
    value=re.sub(r'(?i)((?:api[_-]?key|access_token|credential|secret|token)\s*[:=]\s*["\']?)[^\s,"\'}]+',r'\1[REDACTED]',value)
    return value

class SecureSecrets:
    service='ContentOS/providers'
    cache={}
    def __init__(self,backend=None):self.backend=backend
    def engine(self):
        if self.backend is not None:return self.backend
        if os.environ.get('CONTENT_OS_TEST_NO_KEYCHAIN')=='1':return None
        if sys.platform!='darwin':raise RuntimeError('SECURE_STORE_UNAVAILABLE')
        from keyring.backends.macOS import Keyring
        return Keyring()
    def get(self,pid,field='api_key'):
        try:
            backend=self.engine()
            if not backend:return None
            identity=(id(self.backend) if self.backend else 'MACOS',pid,field)
            if identity not in self.cache:self.cache[identity]=remember(backend.get_password(self.service,f'provider.{pid}.{field}'))
            return self.cache[identity]
        except Exception:return None
    def set(self,pid,value,field='api_key'):
        backend=self.engine()
        if backend is None:raise RuntimeError('SECURE_STORE_UNAVAILABLE')
        try:
            backend.set_password(self.service,f'provider.{pid}.{field}',value);remember(value)
            self.cache[(id(self.backend) if self.backend else 'MACOS',pid,field)]=value
        except Exception:raise RuntimeError('KEYCHAIN_WRITE_FAILED') from None
    def delete(self,pid,field='api_key'):
        self.cache.pop((id(self.backend) if self.backend else 'MACOS',pid,field),None)
        backend=self.engine()
        if backend:
            try:backend.delete_password(self.service,f'provider.{pid}.{field}')
            except Exception:pass

class RedactingFormatter(logging.Formatter):
    def __init__(self,wrapped=None):
        super().__init__();self.wrapped=wrapped or logging.Formatter('%(message)s')
    def format(self,record):
        import copy
        safe=copy.copy(record);safe.msg=redact(safe.msg)
        safe.args=tuple(redact(x) for x in safe.args) if isinstance(safe.args,tuple) else redact(safe.args)
        return redact(self.wrapped.format(safe))
def install_logging_redaction():
    for name in ('','uvicorn','uvicorn.error','uvicorn.access'):
        for handler in logging.getLogger(name).handlers:
            old=handler.formatter
            if not isinstance(old,RedactingFormatter):handler.setFormatter(RedactingFormatter(old))
