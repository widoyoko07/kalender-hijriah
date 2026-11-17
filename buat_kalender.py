"""Buat file .ics kalender Hijriah (Umm al-Qura) untuk diimpor ke kalender Android/Samsung.

Keluaran (folder docs/):
  hijriah-tanggal.ics  - satu event all-day per hari: "5 Jumadil Awal 1448 H"
  hari-penting.ics     - hari besar Islam + puasa sunnah (Senin-Kamis, Ayyamul Bidh, dst.)

Pakai: python buat_kalender.py [tahun_mulai] [tahun_akhir]   (default 2026 2030)
"""
import json
import sys
from types import SimpleNamespace
from datetime import date, timedelta
from pathlib import Path
from hijridate import Gregorian

BULAN = ["Muharram", "Safar", "Rabiul Awal", "Rabiul Akhir", "Jumadil Awal", "Jumadil Akhir",
         "Rajab", "Sya'ban", "Ramadan", "Syawal", "Dzulqa'dah", "Dzulhijjah"]

# (bulan, hari): (judul, kategori)  kategori: besar | puasa | haram
TETAP = {
    (1, 9): ("Puasa Tasu'a", "puasa"),
    (1, 10): ("Puasa Asyura", "puasa"),
    (9, 1): ("Awal Ramadan", "besar"),
    (9, 21): ("Malam Lailatul Qadar (21)", "besar"),
    (9, 23): ("Malam Lailatul Qadar (23)", "besar"),
    (9, 25): ("Malam Lailatul Qadar (25)", "besar"),
    (9, 27): ("Malam Lailatul Qadar (27)", "besar"),
    (9, 29): ("Malam Lailatul Qadar (29)", "besar"),
    (10, 1): ("Idul Fitri (haram puasa)", "haram"),
    (12, 8): ("Puasa Tarwiyah", "puasa"),
    (12, 9): ("Puasa Arafah", "puasa"),
    (12, 10): ("Idul Adha (haram puasa)", "haram"),
    (12, 11): ("Hari Tasyrik (haram puasa)", "haram"),
    (12, 12): ("Hari Tasyrik (haram puasa)", "haram"),
    (12, 13): ("Hari Tasyrik (haram puasa)", "haram"),
}


# Awal bulan Hijriah menurut Kemenag RI (kemenag.json: "tahun-bulan": "YYYY-MM-DD") dipakai untuk hari yang
# sudah berlalu; di luar data itu dipakai Umm al-Qura. Isi kemenag.json setelah sidang isbat / dari kalender Kemenag.
BASE = Path(__file__).parent
KEMENAG = {tuple(map(int, k.split("-"))): date.fromisoformat(v)
           for k, v in json.loads((BASE / "kemenag.json").read_text()).items()}
HARI_INI = date.today()


def hijri(d):
    """(tahun, bulan, hari): Kemenag untuk hari lampau yang datanya ada, selain itu Umm al-Qura."""
    if d <= HARI_INI:
        mulai = [k for k, v in KEMENAG.items() if v <= d]
        if mulai:
            y, m = max(mulai, key=lambda k: KEMENAG[k])
            n = (d - KEMENAG[(y, m)]).days + 1
            if n <= 30:
                return y, m, n
    h = Gregorian.fromdate(d).to_hijri()
    return h.year, h.month, h.day


def esc(s):
    return s.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")


def event(uid, d, judul, ket=""):
    e = [
        "BEGIN:VEVENT",
        f"UID:{uid}@kalender-hijriah",
        "DTSTAMP:20260101T000000Z",
        f"DTSTART;VALUE=DATE:{d:%Y%m%d}",
        f"DTEND;VALUE=DATE:{d + timedelta(days=1):%Y%m%d}",
        f"SUMMARY:{esc(judul)}",
        "TRANSP:TRANSPARENT",
    ]
    if ket:
        e.append(f"DESCRIPTION:{esc(ket)}")
    e.append("END:VEVENT")
    return e


def kalender(nama, isi):
    return "\r\n".join(["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//kalender-hijriah//ID",
                        "CALSCALE:GREGORIAN", f"X-WR-CALNAME:{nama}", *isi, "END:VCALENDAR"]) + "\r\n"


def main():
    t0 = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    t1 = int(sys.argv[2]) if len(sys.argv) > 2 else 2030
    tanggal, penting = [], []
    d = date(t0, 1, 1)
    while d <= date(t1, 12, 31):
        h = SimpleNamespace(**dict(zip(("year", "month", "day"), hijri(d))))
        ymd = f"{d:%Y%m%d}"
        tanggal += event(f"tgl-{ymd}", d, f"{h.day} {BULAN[h.month - 1]} {h.year} H")
        hit = []
        if (h.month, h.day) in TETAP:
            hit.append(TETAP[(h.month, h.day)])
        elif h.month != 9:  # puasa sunnah di luar Ramadan
            haram = h.month == 10 and h.day == 1 or h.month == 12 and h.day >= 10
            if not haram:
                if h.day in (13, 14, 15):
                    hit.append(("Puasa Ayyamul Bidh", "puasa"))
                if d.weekday() in (0, 3):  # Senin, Kamis
                    hit.append(("Puasa Senin" if d.weekday() == 0 else "Puasa Kamis", "puasa"))
                if h.month == 10 and 2 <= h.day <= 7:
                    hit.append(("Puasa Syawal", "puasa"))
        for i, (judul, kat) in enumerate(hit):
            penting += event(f"pnt-{ymd}-{i}", d, judul, f"{h.day} {BULAN[h.month - 1]} {h.year} H")
        d += timedelta(days=1)
    out = BASE / "docs"
    out.mkdir(exist_ok=True)
    (out / "hijriah-tanggal.ics").write_text(kalender("Tanggal Hijriah", tanggal), encoding="utf-8")
    (out / "hari-penting.ics").write_text(kalender("Hari Penting Islam", penting), encoding="utf-8")
    print(f"{t0}-{t1}: {tanggal.count('BEGIN:VEVENT')} hari, {penting.count('BEGIN:VEVENT')} hari penting")


main()
