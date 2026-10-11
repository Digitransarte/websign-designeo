"""Package the reviewed WEB-02 Gutenberg landing theme as an isolated ZIP.

No WordPress writes. Uses the existing immutable source package builder and
applies the native landing contract without changing the stable core builder.
"""
import argparse
import json
import tempfile
from pathlib import Path
from scripts.build_lite_core_library_v01 import build_packages, _load, _zip, ROOT
from scripts.lite_landing_contract_v01 import apply_landing_contract


def build(repo: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError("Refuse to overwrite a theme archive")
    with tempfile.TemporaryDirectory(prefix="web02_landing_") as directory:
        core=Path(directory)/"core.zip"
        library=Path(directory)/"library.zip"
        build_packages(repo, core, library)
        original=_load(core)
        upgraded=apply_landing_contract(original,repo)
        assert set(upgraded)-set(original)=={ROOT+"templates/designeo-landing.html"}
        _zip(output,upgraded)
        if _load(output)!=upgraded:
            raise ValueError("ZIP verification failed")
    return {"artifact":str(output),"files":len(upgraded),
            "native_landing":True,"installed":False,"editor_roundtrip_verified":False}


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    root=Path(__file__).resolve().parents[1]
    print(json.dumps(build(root,args.output.resolve()),indent=2))
