import sys
from fastcore.xtras import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from espatula.processamento import Table

name = "ml"
date = "20240720"
table = Table(name, f"{name}_{date}_smartphone.json")
table.process(tipo_sch="Telefone Móvel Celular")
table.write_excel()
