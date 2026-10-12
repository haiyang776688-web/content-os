"""Keychain first, developer environment fallback. Never serialize credentials."""
import os
from vnext.secrets.secure import remember
class SecretStore:
    def get(self,name):
        if not name:return None
        from vnext.providers.settings import Settings,ROOT
        if ROOT is not None:
            value=Settings().environment(name)
            if value is not None:return remember(value) if name.endswith(('_API_KEY','_KEY','_TOKEN')) else value
        value=os.environ.get(name)
        return remember(value) if name.endswith(('_API_KEY','_KEY','_TOKEN')) else value or None
    def configured(self,name):return bool(name and self.get(name))
