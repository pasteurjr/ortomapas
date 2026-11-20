"""Fetch only the two public Aklavik RGB orthomosaics used by UC-009."""
from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data/validacao/uc009_aklavik"
FILES = [
    ("2022_ortomosaico.tif",
     "https://zenodo.org/records/14608566/files/20220921_DJI_Mini2_UndercoverEisAgenten_Orthomosaic_Aklavik_Town_10cm.tif?download=1",
     710_706_206, "53bf718e84bc8335f54732b554222ed0"),
    ("2024_ortomosaico.tif",
     "https://zenodo.org/records/14608566/files/20240324_DJI_Mini2_UndercoverEisAgenten_Orthomosaic_Aklavik_Town_10cm.tif?download=1",
     710_706_206, "0429640ef35fd1475a54fa33ce8328bb"),
]


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for name, url, expected_size, expected_md5 in FILES:
        target = DEST / name
        if target.exists() and target.stat().st_size == expected_size:
            if md5(target) == expected_md5:
                print(f"OK existente: {target.relative_to(ROOT)} ({expected_size} bytes)")
                continue
            target.unlink()
        partial = target.with_suffix(target.suffix + ".part")
        request = urllib.request.Request(url, headers={"User-Agent": "ortomapas-uc009-validation/1.0"})
        with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as output:
            total = 0
            while block := response.read(4 * 1024 * 1024):
                output.write(block)
                total += len(block)
        if total != expected_size or md5(partial) != expected_md5:
            partial.unlink(missing_ok=True)
            raise RuntimeError(f"Tamanho ou MD5 inválido para {name}; baixados {total} bytes")
        os.replace(partial, target)
        print(f"Baixado e validado: {target.relative_to(ROOT)} ({total} bytes; MD5 correto)")


if __name__ == "__main__":
    main()
