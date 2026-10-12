"""Optional local semantic model. Never downloads a model or uploads local media."""
import os
from pathlib import Path


class LocalEmbeddings:
    models={}

    def configured(self):
        location=os.environ.get('CONTENT_OS_LOCAL_EMBEDDING_MODEL')
        return bool(location and Path(location).expanduser().is_dir())

    def encode(self,texts):
        location=os.environ.get('CONTENT_OS_LOCAL_EMBEDDING_MODEL')
        if not location:return None
        location=str(Path(location).expanduser().resolve())
        if not Path(location).is_dir():raise ValueError('LOCAL_EMBEDDING_MODEL_NOT_FOUND')
        try:from sentence_transformers import SentenceTransformer
        except ImportError as error:raise ValueError('INSTALL_OPTIONAL_SENTENCE_TRANSFORMERS') from error
        if location not in self.models:
            self.models[location]=SentenceTransformer(location,local_files_only=True,device='cpu')
        return {'model_path':location,'method':'LOCAL_SENTENCE_TRANSFORMER',
                'vectors':self.models[location].encode(texts,normalize_embeddings=True).tolist()}
