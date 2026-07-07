from alembic.config import Config
from alembic.script import ScriptDirectory

cfg = Config("alembic.ini")
script = ScriptDirectory.from_config(cfg)

print("Heads:", script.get_heads())
print("Bases:", script.get_bases())

for rev in script.walk_revisions():
    print(rev.revision, rev.down_revision, rev.path)