"""Tool calls are explicit, provenance-carrying and local by default."""
from __future__ import annotations

from pathlib import Path

from vnext.contracts import ToolRequest, ToolResult


class ToolGateway:
    def __init__(self, allowed_roots: list[Path]):
        self.allowed_roots = [root.resolve() for root in allowed_roots]

    def invoke(self, request: ToolRequest) -> ToolResult:
        if request.tool in ("FILE_READ","DOCUMENT_READ","PDF_READ","SNAPSHOT"):
            path = Path(str(request.arguments.get("path", ""))).resolve()
            if not any(path == root or root in path.parents for root in self.allowed_roots):
                return ToolResult(request_id=request.request_id, tool=request.tool, status="BLOCKED", output={"error": "PATH_NOT_ALLOWED"})
            if not path.is_file() or path.stat().st_size > 2_000_000:
                return ToolResult(request_id=request.request_id, tool=request.tool, status="FAILED", output={"error": "MISSING_OR_TOO_LARGE"})
            from vnext.migration.legacy import sha
            pages={}
            if path.suffix.lower()=='.pdf':
                from pypdf import PdfReader
                pages={str(i+1):page.extract_text() or '' for i,page in enumerate(PdfReader(str(path)).pages)}
                text='\n\n'.join(pages.values())
            elif path.suffix.lower()=='.docx':
                from docx import Document
                text='\n'.join(p.text for p in Document(str(path)).paragraphs)
            elif path.suffix.lower() in ('.txt','.md','.json','.html','.htm','.csv'):
                text=path.read_text(errors='replace')
            else:return ToolResult(request_id=request.request_id,tool=request.tool,status='BLOCKED',output={'error':'DOCUMENT_FORMAT_UNSUPPORTED'})
            return ToolResult(request_id=request.request_id,tool=request.tool,status='COMPLETED',output={'text':text,'pages':pages},
                provenance={'path':str(path),'file_hash':sha(path),'snapshot':sha(path),'trust':'UNTRUSTED_SOURCE_DATA','adapter':'LOCAL_DOCUMENT_V1'})
        return ToolResult(request_id=request.request_id, tool=request.tool, status="BLOCKED",
            output={"error": "TOOL_ADAPTER_NOT_CONFIGURED"})
