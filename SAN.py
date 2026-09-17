#!/usr/bin/env python3
# SAN GEMS BNB — lo genius.fun tren BNB Chain. Bean chot 17/09/2026.
#   python3 SAN.py DA-BAO.md
#
# 🔴 DAY LA MAY KHAC HAN MAY ROBINHOOD. Lo nay moi sinh 17/09 nen KHONG con nao
#    "da rot nat, nam li 24 gio" => nam ve cua may cu KHONG dung duoc o day.
#
# BON BUOC (so buoc = thu tu chay):
#   BUOC 1  LAY DANH SACH : API cua lo, 50 con moi nhat                   (1 cu)
#   BUOC 2  LOC THO       : da tot nghiep + tuoi <= TUOI_MAX + loai tu ten (0 cu)
#   BUOC 3  DO SUC HUT TIEN: GeckoTerminal bsc, pool day nhat             (1 cu / 20 con)
#           THUOC A  tien trong pool, XEP HANG TRONG RO (khong phai muc tuyet doi)
#           THUOC B  tien CON VAO TIEP  (so voi anh chup cu trong so)
#           THUOC C  NGUOI MOI vao      (so vi tang, lay tu buoc 1)
#   BUOC 4  CUA AN TOAN   : khoa pool (RPC) + vi to nhat/top10 (GoPlus 56)  (2 cu / con)
#
# 🔑 GIAI DOAN 1 (bay gio): may GHI SO moi luot va in phieu. NGUONG CHUA DUOC DAT —
#    cua vao la XEP HANG TRONG RO cung luot, vi ro co 50 con cung lo cung gio.
#    Ly do: chua co du ca de dat muc tuyet doi (KYLUAT.md muc 11).
import json, time, calendar, sys, os, urllib.request, urllib.error

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
LO     = "https://genius.fun/api/launchpad/v1"
GT     = "https://api.geckoterminal.com/api/v2/networks/bsc"
RPC    = "https://bsc-dataseed.bnbchain.org"
GOPLUS = "https://api.gopluslabs.io/api/v1/token_security/56"

# ---- HA TANG CUA LO genius.fun (dia chi lay tu genius.fun/docs/contracts, da doc ma) ----
LOCKER = "0x60c68b2c6ce7d2268f25a816f326843017d00384"   # giu vi the LP, KHONG co duong rut
HOOK   = "0xff17f41c5efd6cce944af0912f300097d62df5c9"
HATANG = {
    LOCKER: "Locker genius.fun",
    HOOK: "Hook genius.fun",
    "0xff8a2ae655e5851cb414ac5ab41b311da4287281": "Fee escrow",
    "0x6ecbe74e6cf896c610c34a3be59bd54c5a5b784e": "Buyback vault",
    "0xf1200f24c38ddce80a3f0cf26606f047c8ebe49b": "Foundation vault",
    "0x2ef00378984e84f2daa08dfb5fb03bbde2038ae6": "Router",
    "0x78eae9537c0ef90dfe9b7ae964682fe8138afe31": "Factory",
    "0x000000000000000000000000000000000000dead": "vi dot",
}
SEL_ISLOCKED = "0x4a4fbeec"   # isLocked(address)
SEL_LOCKEDSUPPLY = "0x732e78e4"  # lockedTokenSupply(address)
SEL_TOTALSUPPLY = "0x18160ddd"

# ---- SO CUA MAY NAY. 🔴 Khong bang so cua may Robinhood, va chua cai nao duoc do o day ----
TUOI_MAX   = 48.0      # gio. Con gia hon thi khong phai "hang moi cua lo" nua
TOP_RO     = 5         # THUOC A: chi xet N con day tien nhat ro cung luot
CACH_MIN   = 0.5       # THUOC B: anh cu gan hon 30 phut -> qua sat, khong cham
CACH_MAX   = 3.0       # THUOC B: anh cu xa hon 3 gio -> khac tap, khong cham
RES_VO_LY  = 50_000_000  # 🔴 LOC SO VO LY: ca GCAT 17/09 bao doi ung $3,79 ty
RES_SAN    = 20_000    # san tien trong pool, de bo con chi co bui (muc TOT NGHIEP ~ $11K)
VI_TO_MAX  = 5.0       # ⬜ NGUONG NHAP TU MAY ROBINHOOD, CHUA DO TREN BNB
TOP10_MAX  = 25.0      # ⬜ nhu tren
CO_LENH    = 250       # chi de tinh khu hoi UOC, khong phai goi y co lenh
GIO_KHONG_BAO_LAI = 12
GIAN = 2.5 if os.environ.get("GITHUB_ACTIONS") else 2.0
SO_ANH = "DO-DEM.md"
LO_LO  = 20            # GT tokens/multi: 20 dia chi mot cu (an toan hon muc 30)

# 🔴 LOAI THANG TU TEN. Lo nay de ra day token mang ten co phieu that.
CO_PHIEU = {"AAPL","NVDA","TSLA","MSFT","AMZN","META","GOOGL","SPY","QQQ","GLD","MSTR","COIN",
            "HOOD","AMD","INTC","MU","TSM","BTC","ETH","BNB","SOL","USDT","USDC","USD1","XRP",
            "DOGE","OPENAI","ANTHROPIC","SPCX","ZEC"}
T0 = time.time(); CU = [0]


def in_nguong():
    print("SAN GEMS BNB · NGUONG DANG CHAY (Bean chot 17/09) — GIAI DOAN 1: GHI SO, chua co muc tuyet doi")
    print("   BUOC 2 loc tho : da tot nghiep · tuoi <= %.0f gio · tien trong pool >= $%s · loai tu ten"
          % (TUOI_MAX, format(RES_SAN, ",")))
    print("   THUOC A tien vao pool : chi xet %d con day tien nhat RO CUNG LUOT (xep hang, khong phai muc)" % TOP_RO)
    print("   THUOC B con vao tiep  : tien trong pool TANG so anh chup cach %.1f-%.1f gio" % (CACH_MIN, CACH_MAX))
    print("   THUOC C nguoi moi     : so vi TANG so cung anh chup do")
    print("   BUOC 4 cua an toan    : pool phai KHOA (doc isLocked cua locker lo) ·")
    print("                           vi nguoi to nhat <=%.0f%% · top10 <=%.0f%% (GoPlus 56, da loc ha tang)" % (VI_TO_MAX, TOP10_MAX))
    print("   🔴 MA HOP DONG DONG = CANH BAO, KHONG LOAI. Ca lo nay deu ma dong (do 3 con 17/09).")
    print("   🔴 KHU HOI chi la UOC tu TONG POOL — chua do duoc tien doi ung that (viec treo #1).")
    print("   KHONG CO MOC BAN. May in phieu, Bean quyet.")


# ---------- goi mang ----------
def get(url, timeout=25):
    CU[0] += 1
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, json.loads(r.read().decode()), ""
    except urllib.error.HTTPError as e:
        return False, None, "HTTP %d" % e.code
    except Exception as e:
        return False, None, "%s: %s" % (type(e).__name__, e)


def thoang(ly):
    return any(k in ly for k in ("Timeout", "timed out", "HTTP 50", "URLError",
                                 "RemoteDisconnected", "ConnectionReset", "IncompleteRead", "429"))


def get_lai(url, lan=2, timeout=25):
    """LOI GOI KHAC 'khong co du lieu'. Thu lai loi thoang qua."""
    ok, j, ly = get(url, timeout)
    for _ in range(lan):
        if ok:
            break
        if not thoang(ly):
            break
        time.sleep(8)
        ok, j, ly = get(url, timeout)
    return ok, j, ly


def rpc(batch, retry=2):
    CU[0] += 1
    for k in range(retry + 1):
        try:
            req = urllib.request.Request(RPC, data=json.dumps(batch).encode(),
                                         headers={"Content-Type": "application/json", "User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                return True, json.loads(r.read().decode()), ""
        except Exception as e:
            ly = "%s: %s" % (type(e).__name__, e)
            if k == retry:
                return False, None, ly
            time.sleep(5)


def so(x):
    try:
        v = float(x)
        return v
    except (TypeError, ValueError):
        return None


def pad(a):
    return a.lower().replace("0x", "").rjust(64, "0")


# ---------- BUOC 1: DANH SACH TU LO ----------
def danh_sach():
    """Tra ve (danh sach con, ly do loi). File trong bien moi truong LO_FILE thay cho cu goi
    (chi dung khi chay thu o may khong goi duoc lo)."""
    f = os.environ.get("LO_FILE")
    if f and os.path.exists(f):
        j = json.load(open(f, encoding="utf-8"))
        return (j.get("items") or j.get("data") or j), ""
    ok, j, ly = get_lai("%s/launches?limit=50" % LO)
    if not ok:
        return [], ly
    return (j.get("items") or j.get("data") or j or []), ""


def loai_tu_ten(ma):
    return (ma or "").upper() in CO_PHIEU


def loc_tho(ds):
    """0 cu goi. Tra ve (con qua loc, dem tung ly do bi loai)."""
    ra = []
    dem = {"chua tot nghiep": 0, "qua gia": 0, "loai tu ten": 0}
    now = time.time()
    for t in ds:
        if t.get("phase") != "PoolCreated":
            dem["chua tot nghiep"] += 1
            continue
        try:
            sinh = calendar.timegm(time.strptime(t["launched_at"][:19], "%Y-%m-%dT%H:%M:%S"))
        except Exception:
            sinh = now
        tuoi = (now - sinh) / 3600.0
        if tuoi > TUOI_MAX:
            dem["qua gia"] += 1
            continue
        if loai_tu_ten(t.get("symbol")):
            dem["loai tu ten"] += 1
            continue
        ra.append({"ca": (t.get("token") or "").lower(), "ma": t.get("symbol") or "?",
                   "ten": t.get("name") or "", "vi": so(t.get("holders_count")),
                   "mc": so(t.get("market_cap_usd")), "tuoi": tuoi,
                   "deployer": (t.get("deployer") or "").lower()})
    return ra, dem


# ---------- BUOC 3: SUC HUT TIEN ----------
def do_pool(cands):
    """GT bsc tokens/multi, 20 dia chi mot cu. Dat c['res'] = TONG POOL cua pool day nhat.
    🔴 Loc so vo ly TRUOC khi xep hang (ca GCAT bao $3,79 ty ngay 17/09)."""
    loi = []
    for i in range(0, len(cands), LO_LO):
        lo = cands[i:i + LO_LO]
        url = "%s/tokens/multi/%s?include=top_pools" % (GT, ",".join(c["ca"] for c in lo))
        ok, j, ly = get_lai(url)
        time.sleep(GIAN)
        if not ok:
            loi.append("lo %d: %s" % (i // LO_LO + 1, ly))
            for c in lo:
                c["ly_pool"] = "LOI GOI: " + ly
            continue
        inc = {p["id"]: p for p in (j.get("included") or []) if p.get("type") == "pool"}
        theo_ca = {}
        for t in (j.get("data") or []):
            a = t.get("attributes") or {}
            theo_ca[(a.get("address") or "").lower()] = (t, a)
        for c in lo:
            pair = theo_ca.get(c["ca"])
            if not pair:
                c["ly_pool"] = "GT chua co token nay"
                continue
            t, a = pair
            ids = [x["id"] for x in ((((t.get("relationships") or {}).get("top_pools") or {}).get("data")) or [])
                   if x["id"] in inc]
            pools = [inc[x]["attributes"] for x in ids]
            that = [p for p in pools if (so(p.get("reserve_in_usd")) or 0) < RES_VO_LY]
            bo = len(pools) - len(that)
            if not that:
                c["ly_pool"] = "moi pool deu bao so vo ly (>= $%s) — KHONG DO DUOC" % format(RES_VO_LY, ",")
                continue
            p = max(that, key=lambda q: so(q.get("reserve_in_usd")) or 0)
            vol = p.get("volume_usd") or {}
            doi = p.get("price_change_percentage") or {}
            tx = (p.get("transactions") or {}).get("h1") or {}
            c.update({"res": so(p.get("reserve_in_usd")) or 0.0, "pool": p.get("address"),
                      "gia": so(a.get("price_usd")), "fdv": so(a.get("fdv_usd")),
                      "vol1": so(vol.get("h1")) or 0.0, "vol24": so(vol.get("h24")) or 0.0,
                      "m30": so(doi.get("m30")), "h1": so(doi.get("h1")), "h6": so(doi.get("h6")),
                      "h24": so(doi.get("h24")), "mua": tx.get("buys") or 0, "ban": tx.get("sells") or 0,
                      "phi": so(p.get("pool_fee_percentage")), "npool": len(pools), "pool_bo": bo,
                      "ly_pool": ""})
    return loi


def khu_hoi_uoc(res, phi):
    """🔴 UOC, KHONG PHAI CUA CHAN. Tinh tren TONG POOL vi chua doc duoc tien doi ung that
    cua PancakeSwap Infinity (tien nam o kho chung). Thieu ca phi pool khi GT khong khai."""
    if not res:
        return None
    return 4 * CO_LENH / res * 100 + 2 * (phi or 0.0)


# ---------- SO ANH CHUP ----------
def doc_anh_cu(path=SO_ANH):
    """Tra ve {ca: [anh, ...]} — CHI anh co du so (tien trong pool + so vi).
    Anh thieu so thi khong lam moc: bai hoc #22 cua may Robinhood.
    Giu CA DANH SACH, khong chi anh moi nhat: may chay lech nhip hay Bean bam chay tay
    thi anh moi nhat co the cach 0 phut, luc do phai lui ve anh cu hon trong dai."""
    gan = {}
    if not os.path.exists(path):
        return gan
    for dong in open(path, encoding="utf-8"):
        if not dong.startswith("| 20"):
            continue
        o = [x.strip() for x in dong.strip().strip("|").split("|")]
        if len(o) < 6:
            continue
        try:
            g = calendar.timegm(time.strptime(o[0][:16], "%Y-%m-%d %H:%M"))
            ca = o[2].strip("`").lower()
            res = so(o[3].replace("$", "").replace(",", ""))
            vi = so(o[4].replace(",", ""))
            if res is None or vi is None:
                continue
            gan.setdefault(ca, []).append({"gio": g, "res": res, "vi": vi, "ma": o[1]})
        except Exception:
            pass
    for ca in gan:
        gan[ca].sort(key=lambda x: -x["gio"])
    return gan


def chon_anh(ds):
    """Anh MOI NHAT nhung cach it nhat CACH_MIN gio. Ngoai dai thi tra None."""
    if not ds:
        return None, "chua co anh cu co du so"
    now = time.time()
    trong = [a for a in ds if CACH_MIN <= (now - a["gio"]) / 3600.0 <= CACH_MAX]
    if trong:
        return trong[0], ""
    gan_nhat = (now - ds[0]["gio"]) / 3600.0
    return None, "anh cu gan nhat cach %.2f gio, ngoai dai %.1f-%.1f" % (gan_nhat, CACH_MIN, CACH_MAX)


def ghi_anh(rows, path=SO_ANH):
    moi = not os.path.exists(path)
    g = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    with open(path, "a", encoding="utf-8") as f:
        if moi:
            f.write("# SO ANH CHUP — may BNB tu ghi moi luot. CAM sua tay.\n\n")
            f.write("> Muc dich: luot sau biet TIEN TRONG POOL va SO VI tang hay giam.\n")
            f.write("> Day la thu de giai doan 2 dat nguong. Giai doan 1 chua co muc tuyet doi.\n\n")
            f.write("| gio UTC | ma | dia chi | tien trong pool | so vi | von hoa | gia | vol 1h | m30 | h6 | mua/ban h1 | tuoi | hang |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for c in rows:
            f.write("| %s | %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %.1fh | %s |\n" % (
                g, c["ma"], c["ca"],
                ("$" + format(int(c["res"]), ",")) if c.get("res") else "—",
                format(int(c["vi"]), ",") if c.get("vi") else "—",
                ("$" + format(int(c["mc"]), ",")) if c.get("mc") else "—",
                ("%.10g" % c["gia"]) if c.get("gia") else "—",
                ("$" + format(int(c["vol1"]), ",")) if c.get("vol1") else "—",
                ("%+.1f%%" % c["m30"]) if c.get("m30") is not None else "—",
                ("%+.1f%%" % c["h6"]) if c.get("h6") is not None else "—",
                "%s/%s" % (c.get("mua", 0), c.get("ban", 0)),
                c["tuoi"], c.get("hang", "-")))
    return len(rows)


# ---------- BUOC 4: CUA AN TOAN ----------
def khoa_pool(ca):
    """Doc locker cua lo: isLocked + lockedTokenSupply. Tra ve (khoa?, % cung khoa, loi)."""
    ok, d, ly = rpc([
        {"jsonrpc": "2.0", "id": 1, "method": "eth_call",
         "params": [{"to": LOCKER, "data": SEL_ISLOCKED + pad(ca)}, "latest"]},
        {"jsonrpc": "2.0", "id": 2, "method": "eth_call",
         "params": [{"to": LOCKER, "data": SEL_LOCKEDSUPPLY + pad(ca)}, "latest"]},
        {"jsonrpc": "2.0", "id": 3, "method": "eth_call",
         "params": [{"to": ca, "data": SEL_TOTALSUPPLY}, "latest"]}])
    if not ok:
        return None, None, "LOI GOI RPC: " + ly
    g = {}
    for x in d:
        g[x.get("id")] = x.get("result")
    try:
        khoa = int(g[1], 16) == 1
        lk = int(g[2], 16)
        ts = int(g[3], 16)
    except Exception:
        return None, None, "RPC tra ve rong"
    if ts <= 0:
        return None, None, "totalSupply = 0"
    return khoa, lk / ts * 100.0, ""


def goplus(ca_list):
    """MOT cu cho ca lo. Thieu con nao = GoPlus khong co du lieu con do, KHONG phai sach."""
    ra = {}
    if not ca_list:
        return ra, ""
    ok, j, ly = get_lai("%s?contract_addresses=%s" % (GOPLUS, ",".join(ca_list)))
    if not ok:
        return ra, ly
    for k, v in (j.get("result") or {}).items():
        ra[k.lower()] = v
    return ra, ""


def doc_goplus(g):
    """Tra ve (chan?, dong in, vi_to, top10). 🔴 ma dong = CANH BAO, KHONG chan."""
    if g is None:
        return False, "   GOPLUS: ⛔ khong co du lieu con nay — KHONG BIET, khong phai sach", None, None
    canh = []
    if str(g.get("is_open_source", "")).strip() == "0":
        canh.append("ma hop dong DONG (ca lo deu the)")
    for c in ("transfer_pausable", "is_blacklisted", "owner_change_balance", "hidden_owner",
              "can_take_back_ownership", "is_mintable", "selfdestruct"):
        if str(g.get(c, "")).strip() == "1":
            canh.append(c)
    chan = []
    for c in ("is_honeypot", "cannot_sell_all"):
        if str(g.get(c, "")).strip() == "1":
            chan.append(c)
    # vi nguoi = bo ha tang cua lo; giu ca vi 7702 (0xef0100) vi do la VI NGUOI
    nguoi = []
    for h in (g.get("holders") or [])[:10]:
        a = (h.get("address") or "").lower()
        if a in HATANG:
            continue
        if str(h.get("is_contract", "")).strip() == "1":
            continue
        p = so(h.get("percent"))
        if p is not None:
            nguoi.append(p * 100)
    nguoi.sort(reverse=True)
    vi_to = nguoi[0] if nguoi else None
    top10 = sum(nguoi) if nguoi else None
    dong = "   GOPLUS: so vi %s · thue mua/ban %s/%s · vi nguoi to nhat %s · top10 nguoi %s%s" % (
        g.get("holder_count", "?"), g.get("buy_tax", "?"), g.get("sell_tax", "?"),
        ("%.2f%%" % vi_to) if vi_to is not None else "⛔ khong doc duoc",
        ("%.2f%%" % top10) if top10 is not None else "⛔",
        ("\n   ⚠️ " + " · ".join(canh)) if canh else "")
    if chan:
        dong += "\n   🔴 GOPLUS CHAN: " + " · ".join(chan)
    return bool(chan), dong, vi_to, top10


# ---------- SO DA BAO ----------
def doc_da_bao(path):
    cu = {}
    if path and os.path.exists(path):
        for dong in open(path, encoding="utf-8"):
            dong = dong.strip()
            if not dong or dong.startswith("#"):
                continue
            ph = [x.strip() for x in dong.split("|")]
            if len(ph) < 2:
                continue
            try:
                cu[ph[0].lower()] = calendar.timegm(time.strptime(ph[1][:19], "%Y-%m-%dT%H:%M:%SZ"))
            except Exception:
                pass
    return cu


def in_thuoc(c, anh):
    n = lambda x: ("$%.9f" % x).rstrip("0") if x else "?"
    print("   THUOC A tien vao pool: $%s — hang %s/%s trong ro luot nay (cua: top %d)" % (
        format(int(c["res"]), ","), c.get("hang", "?"), c.get("ro", "?"), TOP_RO))
    if not anh:
        print("   THUOC B ⬜ CHUA CO ANH CU co du so — luot dau cua con nay, ghi so de lan sau so")
        print("   THUOC C ⬜ chua cham duoc")
        return
    cach = (time.time() - anh["gio"]) / 3600.0
    print("   (so voi anh chup cach %.1f gio)" % cach)
    d_res = (c["res"] / anh["res"] - 1) * 100 if anh["res"] else None
    d_vi = (c["vi"] / anh["vi"] - 1) * 100 if (anh["vi"] and c.get("vi")) else None
    print("   THUOC B tien con vao : $%s -> $%s (%s) %s" % (
        format(int(anh["res"]), ","), format(int(c["res"]), ","),
        ("%+.1f%%" % d_res) if d_res is not None else "?",
        "✅ con vao" if (d_res or 0) > 0 else "🔴 tien dang ra"))
    print("   THUOC C nguoi moi    : %s -> %s vi (%s) %s" % (
        format(int(anh["vi"]), ","), format(int(c["vi"] or 0), ","),
        ("%+.1f%%" % d_vi) if d_vi is not None else "?",
        "✅ co nguoi moi" if (d_vi or 0) > 0 else "🔴 nguoi ta dang bo di"))


def cham_ba_thuoc(c, gan):
    """Tra ve (dat?, ly do). None = chua cham duoc, KHAC False."""
    if c.get("hang") is None or c["hang"] > TOP_RO:
        return False, "THUOC A truot: khong nam trong top %d tien cua ro" % TOP_RO
    anh, ly = chon_anh(gan.get(c["ca"]))
    c["anh"] = anh
    if not anh:
        return None, ly
    if not anh["res"] or not anh["vi"] or not c.get("vi"):
        return None, "thieu so mot trong hai dau"
    b = c["res"] > anh["res"]
    cc = c["vi"] > anh["vi"]
    if b and cc:
        return True, "tien vao +%.1f%% · vi +%.1f%%" % (
            (c["res"] / anh["res"] - 1) * 100, (c["vi"] / anh["vi"] - 1) * 100)
    return False, "%s%s" % ("" if b else "tien dang ra ", "" if cc else "nguoi dang bo di")


def main():
    so_da_bao = sys.argv[1] if len(sys.argv) > 1 else None
    da_bao = doc_da_bao(so_da_bao)
    gan = doc_anh_cu()
    gio = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    in_nguong()
    ds, ly = danh_sach()
    print("\nPHIEU BNB · %s" % gio)
    if ly:
        print("⛔ LOI GOI API cua lo: %s — KHONG doc thanh 'khong co con nao'" % ly)
        print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))
        return
    print("lo tra ve: %d con" % len(ds))
    if not ds:
        print("⛔ LO TRA VE RONG — loi goi hay lo im, KHONG ket luan.")
        return

    tho, dem = loc_tho(ds)
    print("qua loc tho: %d  (bo: %s)" % (tho and len(tho) or 0,
          " · ".join("%s %d" % (k, v) for k, v in dem.items())))
    if not tho:
        print("KHONG CO GI TRONG DAI")
        print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))
        return

    loi_pool = do_pool(tho)
    for x in loi_pool:
        print("   ⛔ GT %s — LOI GOI, lo nay KHONG duoc do" % x)
    do = [c for c in tho if c.get("res")]
    for c in tho:
        if not c.get("res"):
            print("   ⛔ %s: %s" % (c["ma"], c.get("ly_pool") or "khong do duoc"))
    print("do duoc pool: %d" % len(do))
    do = [c for c in do if c["res"] >= RES_SAN]
    print("con tien trong pool >= $%s: %d" % (format(RES_SAN, ","), len(do)))
    if not do:
        print("da ghi %d dong anh chup vao %s" % (ghi_anh([c for c in tho if c.get("res")]), SO_ANH))
        print("KHONG CO UNG VIEN")
        print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))
        return

    # XEP HANG TRONG RO — day la "cua" cua giai doan 1
    do.sort(key=lambda c: -c["res"])
    for i, c in enumerate(do, 1):
        c["hang"] = i
        c["ro"] = len(do)

    nguong_bao = time.time() - GIO_KHONG_BAO_LAI * 3600
    ung = []
    top = [c for c in do if c["hang"] <= TOP_RO]
    gp, gp_loi = goplus([c["ca"] for c in top])
    if gp_loi:
        print("   ⛔ GoPlus LOI GOI: %s — KHONG doc thanh 'sach'" % gp_loi)
    else:
        print("GoPlus: doc duoc %d/%d con" % (len(gp), len(top)))

    for c in top:
        dat, ly_thuoc = cham_ba_thuoc(c, gan)
        print("\n%s  %s   (%s)" % (c["ma"], c["ca"], c.get("ten") or ""))
        print("   von hoa $%s · gia %s · tuoi %.1f gio · pool %s · %d pool cung token%s" % (
            format(int(c["mc"] or 0), ","), ("%.10g" % c["gia"]) if c.get("gia") else "?",
            c["tuoi"], (c.get("pool") or "?")[:12], c.get("npool", 0),
            (" · bo %d pool bao so vo ly" % c["pool_bo"]) if c.get("pool_bo") else ""))
        print("   doi gia: m30 %s · h1 %s · h6 %s · h24 %s · vol 1h $%s · mua/ban h1 %d/%d" % (
            ("%+.1f%%" % c["m30"]) if c.get("m30") is not None else "?",
            ("%+.1f%%" % c["h1"]) if c.get("h1") is not None else "?",
            ("%+.1f%%" % c["h6"]) if c.get("h6") is not None else "?",
            ("%+.1f%%" % c["h24"]) if c.get("h24") is not None else "?",
            format(int(c.get("vol1") or 0), ","), c.get("mua", 0), c.get("ban", 0)))
        in_thuoc(c, c.get("anh"))

        if c["ca"] in da_bao and da_bao[c["ca"]] >= nguong_bao:
            print("   BO QUA: da bao trong %d gio qua" % GIO_KHONG_BAO_LAI)
            continue

        khoa, pct, loi_khoa = khoa_pool(c["ca"])
        time.sleep(0.5)
        if loi_khoa:
            print("   CUA AN TOAN ⛔ %s" % loi_khoa)
            continue
        if not khoa:
            print("   CUA AN TOAN 🔴 LOAI: locker cua lo bao pool CHUA KHOA")
            continue
        print("   CUA AN TOAN: pool DA KHOA, locker giu %.2f%% cung (khong co duong rut — da doc ma)" % pct)
        chan, dong_gp, vi_to, top10 = doc_goplus(gp.get(c["ca"]))
        print(dong_gp)
        if chan:
            print("   🔴 LOAI O CUA AN TOAN — GoPlus chan")
            continue
        if vi_to is None:
            print("   ⛔ khong doc duoc phan bo vi — KHONG ket luan sach")
        elif vi_to > VI_TO_MAX or (top10 or 0) > TOP10_MAX:
            print("   🔴 LOAI O CUA AN TOAN — phan bo: vi to nhat %.2f%% / top10 %.2f%%" % (vi_to, top10 or 0))
            continue

        kh = khu_hoi_uoc(c["res"], c.get("phi"))
        print("   KHU HOI UOC $%d: %.2f%% — ⬜ UOC tu TONG POOL, chua do tien doi ung that%s" % (
            CO_LENH, kh, "" if c.get("phi") is not None else " (GT khong khai phi pool)"))
        if dat is True:
            ung.append(c)
            print("   ⇒ UNG VIEN 3/3 — dung dau ro, tien con vao, co nguoi moi (%s)" % ly_thuoc)
            if c.get("gia"):
                dat_gia = c["gia"] * (1 + kh / 200)
                print("   GIA DAT LENH: %s  = gia nay + %.3f%% truot chieu MUA" % (
                    ("$%.10g" % dat_gia), kh / 2))
            print("   ⏰ GIO IN PHIEU: %s — vao muon hon thi DO LAI truoc" % gio)
            print("   DONG DAN VAO SO DA BAO: %s | %s | %s" % (
                c["ca"], time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), c["ma"]))
        elif dat is None:
            print("   ⇒ THEO DOI — qua cua an toan, nhung %s" % ly_thuoc)
        else:
            print("   ⇒ KHONG VAO — %s" % ly_thuoc)

    print("\nda ghi %d dong anh chup vao %s" % (ghi_anh([c for c in tho if c.get("res")]), SO_ANH))
    print("UNG VIEN 3/3: %d · %s" % (len(ung), " ".join(c["ma"] for c in ung) or "—"))
    if not ung:
        print("KHONG CO UNG VIEN MOI")
    print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))


main()
