"""
سكريبت تحميل قواعد بيانات إعراب القرآن الكريم
يُشغَّل مرة واحدة قبل تشغيل الـ API
"""
import os
import urllib.request
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "إعراب_القرآن_الكريم")

FILES = [
    {
        "name": "irab_al_karbasi.db",
        "url": "https://raw.githubusercontent.com/app-furqan/quran-app-data/main/data/irab_al_karbasi.tar.xz",
        "compressed": True,
        "format": "tar.xz",
    },
    {
        "name": "MASAQ.db",
        "url": "https://data.mendeley.com/public-files/datasets/9yvrzxktmr/files/5bc583ff-4c7f-4a1f-a12a-47f89afc5c91/file_downloaded",
        "compressed": False,
    },
]


def download(name: str, url: str, compressed: bool = False, fmt: str = ""):
    dest = os.path.join(DATA_DIR, name)
    if os.path.exists(dest):
        print(f"✓ {name} موجود مسبقاً")
        return

    print(f"⬇ تحميل {name} ...")
    tmp = dest + (".tmp" + ("." + fmt if fmt else ""))
    try:
        urllib.request.urlretrieve(url, tmp)
    except Exception as e:
        print(f"✗ فشل تحميل {name}: {e}", file=sys.stderr)
        return

    if compressed and fmt == "tar.xz":
        import tarfile
        with tarfile.open(tmp, "r:xz") as t:
            for m in t.getmembers():
                m.name = os.path.basename(m.name)
                t.extract(m, DATA_DIR)
        os.remove(tmp)
    else:
        os.rename(tmp, dest)

    print(f"✓ {name} جاهز")


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    for f in FILES:
        download(f["name"], f["url"], f.get("compressed", False), f.get("format", ""))
    print("\nجميع الملفات جاهزة. شغّل الآن: python main.py")
