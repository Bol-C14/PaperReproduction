"""Read-only DCP screening, no Vivado/API calls; run using configured APRIL Python."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

for name in sys.argv[1:]:
    path = Path(name)
    with ZipFile(path) as archive:
        meta = ET.fromstring(archive.read("dcp.xml"))
        edif_name = next(n for n in archive.namelist() if n.endswith(".edf"))
        edif = archive.read(edif_name)
        text = edif.decode(errors="replace")
        record = {
            "file": path.name,
            "bytes": path.stat().st_size,
            "dcp_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "edif_sha256": hashlib.sha256(edif).hexdigest(),
            "edif_bytes": len(edif),
            "instance_tokens": text.count("(instance "),
            "port_tokens": text.count("(port "),
            "part": meta.find("Part").get("Name"),
            "product": meta.find("PRODUCT").get("Name"),
            "top": meta.find("Top").get("Name"),
            "note": "Lexical screening counts, not semantic/equivalence evidence",
        }
        print(json.dumps(record, sort_keys=True))
