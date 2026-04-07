from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "dist" / "raw"
OUT_DIR = ROOT / "release"

LISTS = {
    "private": "DIRECT",
    "category-ru": "DIRECT",
    "apple": "DIRECT",
    "twitch": "DIRECT",
    "youtube": "PROXY",
    "category-ban-ru": "PROXY",
}

TYPE_MAP = {
    "domain": "DOMAIN-SUFFIX",
    "full": "DOMAIN",
    "keyword": "DOMAIN-KEYWORD",
    "regexp": "DOMAIN-REGEX",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def convert_line(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    line = line.split(":@", 1)[0]

    if ":" not in line:
        return None

    kind, value = line.split(":", 1)
    kind = kind.strip().lower()
    value = value.strip()

    mapped = TYPE_MAP.get(kind)
    if not mapped or not value:
        return None

    return f"{mapped},{value}"


def convert_file(src: Path, dst: Path) -> None:
    rules = set()

    for line in src.read_text(encoding="utf-8").splitlines():
        converted = convert_line(line)
        if converted:
            rules.add(converted)

    dst.write_text(
        "\n".join(sorted(rules)) + "\n",
        encoding="utf-8",
    )


def make_raw_url(filename: str) -> str:
    repo = os.environ.get("GITHUB_REPOSITORY", "YOUR_USER/YOUR_REPO")
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/release/{filename}"


def build_example_conf() -> str:
    return f"""[General]
bypass-system = true
skip-proxy = 127.0.0.1, localhost, *.local, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12

[Rule]
IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
IP-CIDR,172.16.0.0/12,DIRECT,no-resolve
IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
IP-CIDR,127.0.0.0/8,DIRECT,no-resolve
IP-CIDR,169.254.0.0/16,DIRECT,no-resolve

RULE-SET,{make_raw_url("private.list")},DIRECT
RULE-SET,{make_raw_url("category-ru.list")},DIRECT
RULE-SET,{make_raw_url("apple.list")},DIRECT
RULE-SET,{make_raw_url("twitch.list")},DIRECT

RULE-SET,{make_raw_url("youtube.list")},PROXY,force-remote-dns
RULE-SET,{make_raw_url("category-ban-ru.list")},PROXY,force-remote-dns

GEOIP,RU,DIRECT
FINAL,PROXY
"""


def main() -> None:
    ensure_dir(OUT_DIR)

    available = sorted(p.name for p in RAW_DIR.glob("*.txt"))

    for name in LISTS:
        src = RAW_DIR / f"{name}.txt"
        dst = OUT_DIR / f"{name}.list"

        if not src.exists():
            raise FileNotFoundError(
                f"Missing source list: {src}. Available files: {available}"
            )

        convert_file(src, dst)

    (OUT_DIR / "example-shadowrocket.conf").write_text(
        build_example_conf(),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
