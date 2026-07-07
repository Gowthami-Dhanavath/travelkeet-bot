from alembic.config import Config
from alembic.script import ScriptDirectory

cfg = Config("alembic.ini")
script = ScriptDirectory.from_config(cfg)

print("Script location:", script.dir)

print("\nRevision files found:")
for rev in script.walk_revisions():
    print(rev.revision, rev.path)

print("\nFilesystem contents:")
import os
for root, dirs, files in os.walk(script.dir):
    for f in files:
        print(os.path.join(root, f))