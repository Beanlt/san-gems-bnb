#!/usr/bin/env python3
# SAN GEMS BNB — lo genius.fun tren BNB Chain. Bean chot 17/09/2026, va 18/09 (v2).
#   python3 SAN.py DA-BAO.md
#
# 🔴 DAY LA MAY KHAC HAN MAY ROBINHOOD. Lo nay moi sinh 17/09 nen KHONG con nao
#    "da rot nat, nam li 24 gio" => nam ve cua may cu KHONG dung duoc o day.
#
# BON BUOC (so buoc = thu tu chay):
#   BUOC 1  LAY DANH SACH : API cua lo, 50 con moi nhat, THU NHIEU KIEU HEADER      (1-4 cu)
#   BUOC 2  LOC THO       : da tot nghiep + tuoi <= TUOI_MAX + loai tu ten          (0 cu)
#   BUOC 3  DO SUC HUT TIEN: GeckoTerminal bsc, GOI TUNG CON, chon POOL CUA LO      (1-3 cu / con)
#           THUOC A  tien trong POOL CUA LO, XEP HANG TRONG RO (khong phai muc tuyet doi)
#           THUOC B  tien CON VAO TIEP  (so voi anh chup cu CUA CUNG MOT POOL)
#           THUOC C  NGUOI MOI vao      (so vi tang, lay tu buoc 1)
#   BUOC 4  CUA AN TOAN   : khoa pool (RPC) + vi to nhat/top10 (GoPlus 56, TUNG CON)
#
# 🔑 GIAI DOAN 1 (bay gio): may GHI SO moi luot va in phieu. NGUONG CHUA DUOC DAT —
#    cua vao la XEP HANG TRONG RO cung luot, vi ro co 50 con cung lo cung gio.
#    Ly do: chua co du ca de dat muc tuyet doi (KYLUAT.md muc 11).
#
# v2 (18/09) va bon lo hong do duoc ngay 18/09, chi tiet o SCRIPT.md muc 0.2 va 4.1:
#   D1 tokens/multi chi tra 1 pool moi con  -> doi sang tokens/<ca>/pools, co phan trang
#   D2 pool sau nhat KHONG con la pool cua lo -> chon pool sau nhat tren pancakeswap-infinity
#   D3 so anh chup khong ghi pool            -> them cot pool va san, thuoc B chi cham CUNG POOL
#   D4 GoPlus goi ca lo tra ve thieu         -> goi TUNG CON
#   va: buoc 1 hong thi in bang CONG de biet cho nao tac, khong doan.
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
PHI_LO     = 2.0       # 🆕 PHI GIAO DICH CUA LO, mot chieu, %. Trang token cua lo khai thang:
                       #    "TOTAL TRADING FEE 2%" = foundation 1 + nguoi tao 0,25 + san 0,5 + mua lai 0,25.
                       #    GeckoTerminal de o phi RONG cho moi pool cua lo => truoc day may tinh thanh 0.
GIO_KHONG_BAO_LAI = 12
GIAN = 2.5 if os.environ.get("GITHUB_ACTIONS") else 2.0
GT_GIAN = 4.0          # 🆕 giãn moi cu GeckoTerminal. Do 18/09: ~12 cu cach 2,2 giay la an 429
GP_GIAN = 1.2          # 🆕 giãn moi cu GoPlus khi goi tung con
TRANG_POOL = 3         # 🆕 so trang toi da cua tokens/<ca>/pools (20 pool moi trang)
SO_ANH = "DO-DEM.md"
LO_LO  = 20            # giu lai: tran cu cua tokens/multi, nay khong dung nua
T0 = time.time(); CU = [0]

# 🔴 LOAI THANG TU TEN. Lo nay de ra day token mang ten co phieu that.
CO_PHIEU = {"AAPL","NVDA","TSLA","MSFT","AMZN","META","GOOGL","SPY","QQQ","GLD","MSTR","COIN",
            "HOOD","AMD","INTC","MU","TSM","BTC","ETH","BNB","SOL","USDT","USDC","USD1","XRP",
            "DOGE","OPENAI","ANTHROPIC","SPCX","ZEC"}

# 🆕 SAN CUA LO. Pool cua lo la pool SAU NHAT nam tren san co tien to nay.
#    Da kiem 1 ca 18/09: GSTOCK ra dung pool id 0x6a81b1cd...cec2de3 ghi trong HOSO.md 4.1.
SAN_LO = "pancakeswap-infinity"

# 🆕 BON KIEU HEADER cho cong cua lo, thu lan luot. May GitHub bi 403 hai luot lien
#    (17/09 23:39 va 18/09 13:47) trong khi Chrome cua Bean goi 200. Luot dau chay ban nay
#    se cho biet 403 la do header hay do dai IP trung tam du lieu.
LO_KIEU = [
    ("tran", {"User-Agent": UA, "Accept": "application/json"}),
    ("day du", {"User-Agent": UA, "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.9", "Referer": "https://genius.fun/",
                "Origin": "https://genius.fun",
                "sec-ch-ua": '"Chromium";v="131", "Not_A Brand";v="24"',
                "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
                "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Site": "same-origin"}),
    ("khong UA", {"Accept": "application/json"}),
    ("curl", {"User-Agent": "curl/8.5.0", "Accept": "*/*"}),
]


def in_nguong():
    print("SAN GEMS BNB · NGUONG DANG CHAY (Bean chot 17/09, ban v2 18/09) — GIAI DOAN 1: GHI SO, chua co muc tuyet doi")
    print("   BUOC 2 loc tho : da tot nghiep · tuoi <= %.0f gio · tien trong pool >= $%s · loai tu ten"
          % (TUOI_MAX, format(RES_SAN, ",")))
    print("   THUOC A tien vao pool : chi xet %d con day tien nhat RO CUNG LUOT (xep hang, khong phai muc)" % TOP_RO)
    print("   THUOC B con vao tiep  : tien trong pool TANG so anh chup cach %.1f-%.1f gio" % (CACH_MIN, CACH_MAX))
    print("   THUOC C nguoi moi     : so vi TANG so cung anh chup do")
    print("   BUOC 4 cua an toan    : pool phai KHOA (doc isLocked cua locker lo) ·")
    print("                           vi nguoi to nhat <=%.0f%% · top10 <=%.0f%% (GoPlus 56, da loc ha tang)" % (VI_TO_MAX, TOP10_MAX))
    print("   🔴 MA HOP DONG DONG = CANH BAO, KHONG LOAI. Ca lo nay deu ma dong (do 3 con 17/09).")
    print("   🔴 KHU HOI chi la UOC tu TONG POOL — chua do duoc tien doi ung that (viec treo #1).")
    print("   🆕 THUOC A do POOL CUA LO (san '%s'), KHONG do pool sau nhat cua ben thu ba." % SAN_LO)
    print("   🆕 THUOC B chi cham khi anh cu la CUNG MOT POOL. Khac pool -> ⬜ khong cham.")
    print("   🆕 THUOC B do bang DON VI TOKEN DOI UNG (bStock), KHONG do bang USD —")
    print("      pool cua lo cap voi NVDAB/AAPLB/BNCB... nen gia co phieu doi la so USD nhay theo.")
    print("   KHONG CO MOC BAN. May in phieu, Bean quyet.")


# ---------- goi mang ----------
def get(url, timeout=25, headers=None):
    CU[0] += 1
    try:
        hd = headers or {"User-Agent": UA, "Accept": "application/json"}
        req = urllib.request.Request(url, headers=hd)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return True, json.loads(r.read().decode()), ""
    except urllib.error.HTTPError as e:
        return False, None, "HTTP %d" % e.code
    except Exception as e:
        return False, None, "%s: %s" % (type(e).__name__, e)


def thoang(ly):
    return any(k in ly for k in ("Timeout", "timed out", "HTTP 50", "URLError",
                                 "RemoteDisconnected", "ConnectionReset", "IncompleteRead", "429"))


def get_lai(url, lan=2, timeout=25, headers=None):
    """LOI GOI KHAC 'khong co du lieu'. Thu lai loi thoang qua.
    429 cua GeckoTerminal la loi goi, nghi lau hon roi goi lai (SCRIPT.md 7.3)."""
    ok, j, ly = get(url, timeout, headers)
    for _ in range(lan):
        if ok:
            break
        if not thoang(ly):
            break
        time.sleep(45 if "429" in ly else 8)
        ok, j, ly = get(url, timeout, headers)
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


def in_cong():
    """🆕 Chay KHI BUOC 1 HONG. In xem cong nao song, de lan sau khoi phai doan.
    Moi dong la mot phep do that, khong phai suy luan."""
    print("\n   --- BANG CONG, do ngay tai day ---")
    ok, _, ly = get_lai("%s/tokens/multi/%s?include=top_pools" % (GT, HOOK))
    print("   GeckoTerminal : %s" % ("OK" if ok else "⛔ " + ly))
    ok, d, ly = rpc([{"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber", "params": []}])
    print("   RPC eth_call  : %s" % ("OK, khoi %s" % (d[0].get("result") if ok and d else "?") if ok else "⛔ " + ly))
    ok, d, ly = rpc([{"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
                      "params": [{"address": LOCKER, "fromBlock": "latest", "toBlock": "latest"}]}])
    ghi = "⛔ " + ly
    if ok and d:
        ghi = "⛔ " + str(d[0].get("error")) if d[0].get("error") else "OK"
    print("   RPC getLogs   : %s" % ghi)
    ok, _, ly = get_lai("%s?contract_addresses=%s" % (GOPLUS, "0x55d398326f99059ff775485246999027b3197955"))
    print("   GoPlus        : %s" % ("OK" if ok else "⛔ " + ly))
    print("   --- het bang cong ---")


# ---------- BUOC 1: DANH SACH TU LO ----------
def danh_sach():
    """Tra ve (danh sach con, ly do loi). File trong bien moi truong LO_FILE thay cho cu goi
    (chi dung khi chay thu o may khong goi duoc lo).
    🆕 Thu lan luot cac kieu header o LO_KIEU, in ma tra ve tung kieu."""
    f = os.environ.get("LO_FILE")
    if f and os.path.exists(f):
        j = json.load(open(f, encoding="utf-8"))
        return (j.get("items") or j.get("data") or j), ""
    url = "%s/launches?limit=50" % LO
    lydo = []
    for ten, hd in LO_KIEU:
        ok, j, ly = get_lai(url, headers=hd)
        print("   cong lo · header kieu %-9s -> %s" % (ten, "OK" if ok else ly))
        if ok:
            return (j.get("items") or j.get("data") or j or []), ""
        lydo.append("%s=%s" % (ten, ly))
        time.sleep(2)
    return [], " · ".join(lydo)


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
def moi_pool(ca):
    """🆕 D1: tokens/<ca>/pools co phan trang. tokens/multi chi tra 1 pool moi con (do 18/09).
    Tra ve (danh sach pool, ly do loi)."""
    ra = []
    for trang in range(1, TRANG_POOL + 1):
        ok, j, ly = get_lai("%s/tokens/%s/pools?page=%d" % (GT, ca, trang))
        time.sleep(GT_GIAN)
        if not ok:
            return ra, ly
        d = j.get("data") or []
        ra += d
        if len(d) < 20:
            break
    return ra, ""


def so_bo(cands):
    """🆕 LOC SO BO — 1 cu cho ca lo, chi de BOT SO CON phai goi rieng.
    tokens/multi tra ve DUNG 1 pool moi con (D1), va pool do la pool GT xep dau.
    Pool cua lo la MOT trong cac pool cua con do, nen no khong the day hon pool sau nhat.
    => con nao pool GT xep dau da duoi RES_SAN thi pool cua lo cung duoi RES_SAN.
    ⬜ Gia dinh 'GT xep dau = pool sau nhat' moi kiem duoc 1 ca (GSTOCK 18/09).
       Con nao goi hong thi GIU LAI, khong duoc loai im lang."""
    for i in range(0, len(cands), LO_LO):
        lo = cands[i:i + LO_LO]
        url = "%s/tokens/multi/%s?include=top_pools" % (GT, ",".join(c["ca"] for c in lo))
        ok, j, ly = get_lai(url)
        time.sleep(GT_GIAN)
        if not ok:
            for c in lo:
                c["res_tho"] = None
                c["ly_tho"] = "LOI GOI: " + ly
            continue
        inc = {p["id"]: p for p in (j.get("included") or []) if p.get("type") == "pool"}
        theo = {}
        for t in (j.get("data") or []):
            ca = ((t.get("attributes") or {}).get("address") or "").lower()
            best = 0.0
            for x in ((((t.get("relationships") or {}).get("top_pools") or {}).get("data")) or []):
                p = inc.get(x["id"])
                if not p:
                    continue
                v = so((p.get("attributes") or {}).get("reserve_in_usd")) or 0.0
                if v < RES_VO_LY and v > best:
                    best = v
            theo[ca] = best
        for c in lo:
            c["res_tho"] = theo.get(c["ca"])
            c["ly_tho"] = "" if c["res_tho"] is not None else "GT chua co token nay"


def do_pool(cands):
    """🆕 Goi TUNG CON. Dat:
         c['res']  = tien trong POOL CUA LO  (day la so cua THUOC A)
         c['ngoai']= tien trong pool sau nhat KHONG phai cua lo, de Bean thay chenh lech
       🔴 Loc so vo ly TRUOC khi chon (ca GCAT bao $3,79 ty ngay 17/09)."""
    loi = []
    for c in cands:
        pools, ly = moi_pool(c["ca"])
        if ly:
            c["ly_pool"] = "LOI GOI: " + ly
            loi.append("%s: %s" % (c["ma"], ly))
            continue
        if not pools:
            c["ly_pool"] = "GT chua co pool nao cua token nay"
            continue
        that, bo = [], 0
        for p in pools:
            v = so((p.get("attributes") or {}).get("reserve_in_usd")) or 0.0
            if v >= RES_VO_LY:
                bo += 1
                continue
            that.append(p)
        if not that:
            c["ly_pool"] = "moi pool deu bao so vo ly (>= $%s) — KHONG DO DUOC" % format(RES_VO_LY, ",")
            continue
        def san(p):
            return (((p.get("relationships") or {}).get("dex") or {}).get("data") or {}).get("id") or "?"
        def tien(p):
            return so((p.get("attributes") or {}).get("reserve_in_usd")) or 0.0
        cua_lo = [p for p in that if san(p).startswith(SAN_LO)]
        ben_ngoai = [p for p in that if not san(p).startswith(SAN_LO)]
        if not cua_lo:
            c["ly_pool"] = "⛔ khong thay pool nao cua lo (san '%s') — KHONG DO DUOC" % SAN_LO
            continue
        p = max(cua_lo, key=tien)
        q = max(ben_ngoai, key=tien) if ben_ngoai else None
        a = p.get("attributes") or {}
        vol = a.get("volume_usd") or {}
        tx = (a.get("transactions") or {}).get("h1") or {}
        # 🔴 Pool cua lo hay cap kieu "B13B / GSTOCK" — con MINH nam o VE QUOTE.
        #    `price_change_percentage` cua GT la cua ve BASE. Lay bua la in ra doi gia cua
        #    token khac. Nen: chi lay gia va doi gia tu pool ma MINH LA BASE, doi chieu du
        #    42 ky tu. Khong co pool nao nhu the thi ghi ⬜, KHONG doan.
        def la_base(x):
            i = ((((x.get("relationships") or {}).get("base_token") or {}).get("data") or {}).get("id") or "").lower()
            return i.endswith(c["ca"])
        # 🆕 D5: pool cua lo cap voi bStock (NVDAB, AAPLB, BNCB...). reserve_in_usd NHAY khi
        #     GIA CO PHIEU DOI UNG doi, du khong ai mua ban con meme. Quy ve DON VI DOI UNG thi
        #     mien nhiem: res_q = reserve_in_usd / gia_doi_ung.
        p_la_base = ((((p.get("relationships") or {}).get("base_token") or {}).get("data") or {}).get("id") or "").lower().endswith(c["ca"])
        gia_doi = so(a.get("quote_token_price_usd")) if p_la_base else so(a.get("base_token_price_usd"))
        ten_pool = a.get("name") or ""
        doi_ung = "?"
        for phan in [x.strip() for x in ten_pool.split("/")]:
            if phan and phan.split()[0].upper() != (c["ma"] or "").upper():
                doi_ung = phan.split()[0]
                break
        res_q = (tien(p) / gia_doi) if gia_doi else None

        base_pools = [x for x in that if la_base(x)]
        r = max(base_pools, key=tien) if base_pools else None
        ra_ = (r.get("attributes") or {}) if r else {}
        doi = (ra_.get("price_change_percentage") or {}) if r else {}
        c.update({"res": tien(p), "pool": a.get("address"), "san": san(p),
                  "doi_ung": doi_ung, "gia_doi": gia_doi, "res_q": res_q,
                  "gia": so(ra_.get("base_token_price_usd")) if r else None,
                  "gia_pool": (ra_.get("address") if r else None),
                  "vol1": so(vol.get("h1")) or 0.0, "vol24": so(vol.get("h24")) or 0.0,
                  "m30": so(doi.get("m30")), "h1": so(doi.get("h1")), "h6": so(doi.get("h6")),
                  "h24": so(doi.get("h24")), "mua": tx.get("buys") or 0, "ban": tx.get("sells") or 0,
                  "phi": so(a.get("pool_fee_percentage")), "npool": len(pools), "pool_bo": bo,
                  "ngoai": tien(q) if q else 0.0,
                  "ngoai_ten": ((q.get("attributes") or {}).get("name") if q else ""),
                  "ngoai_san": san(q) if q else "",
                  "ly_pool": ""})
    return loi


def khu_hoi_uoc(res, phi):
    """🔴 UOC, KHONG PHAI CUA CHAN. Tinh tren TONG POOL vi chua doc duoc tien doi ung that
    cua PancakeSwap Infinity (tien nam o kho chung).
    🆕 18/09: GT de o phi RONG cho MOI pool cua lo, nen truoc day ham nay cong 0 phi va
    bao khu hoi thap hon THAT hon ba lan. Trang token cua lo khai 2% moi chieu => dung PHI_LO
    lam phi mac dinh khi GT khong khai."""
    if not res:
        return None
    p = phi if phi is not None else PHI_LO
    return 4 * CO_LENH / res * 100 + 2 * p


# ---------- SO ANH CHUP ----------
def doc_anh_cu(path=SO_ANH):
    """Tra ve {ca: [anh, ...]} — CHI anh co du so (tien trong pool + so vi).
    Anh thieu so thi khong lam moc: bai hoc #22 cua may Robinhood.
    Giu CA DANH SACH, khong chi anh moi nhat: may chay lech nhip hay Bean bam chay tay
    thi anh moi nhat co the cach 0 phut, luc do phai lui ve anh cu hon trong dai.
    🆕 D3+D5: doc duoc BA kieu dong — kieu v1 13 cot (khong co pool), kieu v2 15 cot (co pool),
    kieu v3 17 cot (them 'doi ung' + 'res doi ung'). Chi dong v3 moi cham duoc thuoc B bang
    DON VI DOI UNG; dong cu hon thi lui ve do bang USD va phieu in canh bao."""
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
            doi = None; res_q = None
            if len(o) >= 17:          # kieu v3: co cot 'doi ung' va 'res doi ung'
                pool = o[3].strip("`").lower() or None
                doi = o[5] or None
                res = so(o[6].replace("$", "").replace(",", ""))
                res_q = so(o[7].replace(",", ""))
                vi = so(o[8].replace(",", ""))
            elif len(o) >= 15:        # kieu v2: co pool, chua co doi ung
                pool = o[3].strip("`").lower() or None
                res = so(o[5].replace("$", "").replace(",", ""))
                vi = so(o[6].replace(",", ""))
            else:                     # kieu v1: chua co pool
                pool = None
                res = so(o[3].replace("$", "").replace(",", ""))
                vi = so(o[4].replace(",", ""))
            if res is None or vi is None:
                continue
            gan.setdefault(ca, []).append({"gio": g, "res": res, "vi": vi, "ma": o[1],
                                           "pool": pool, "doi": doi, "res_q": res_q})
        except Exception:
            pass
    for ca in gan:
        gan[ca].sort(key=lambda x: -x["gio"])
    return gan


def chon_anh(ds, pool=None):
    """Anh MOI NHAT nhung cach it nhat CACH_MIN gio. Ngoai dai thi tra None.
    🆕 D3: anh phai la CUNG MOT POOL. Anh khong ghi pool (dong kieu cu) thi khong dung."""
    if not ds:
        return None, "chua co anh cu co du so"
    now = time.time()
    trong = [a for a in ds if CACH_MIN <= (now - a["gio"]) / 3600.0 <= CACH_MAX]
    if not trong:
        gan_nhat = (now - ds[0]["gio"]) / 3600.0
        return None, "anh cu gan nhat cach %.2f gio, ngoai dai %.1f-%.1f" % (gan_nhat, CACH_MIN, CACH_MAX)
    cung = [a for a in trong if a.get("pool") and pool and a["pool"] == (pool or "").lower()]
    if not cung:
        return None, "co anh trong dai nhung KHAC POOL (hay anh cu khong ghi pool) — khong cham"
    return cung[0], ""


def ghi_anh(rows, path=SO_ANH):
    """🆕 D3: them cot 'pool' va 'san'. Dong cu 13 cot van doc duoc, xem doc_anh_cu."""
    moi = not os.path.exists(path)
    g = time.strftime("%Y-%m-%d %H:%M", time.gmtime())
    with open(path, "a", encoding="utf-8") as f:
        if moi:
            f.write("# SO ANH CHUP — may BNB tu ghi moi luot. CAM sua tay.\n\n")
            f.write("> Muc dich: luot sau biet TIEN TRONG POOL va SO VI tang hay giam.\n")
            f.write("> Day la thu de giai doan 2 dat nguong. Giai doan 1 chua co muc tuyet doi.\n")
            f.write("> Cot 'pool' la POOL CUA LO. Thuoc B chi cham khi hai anh CUNG mot pool.\n\n")
            f.write("| gio UTC | ma | dia chi | pool | san | doi ung | tien trong pool | res doi ung | so vi | von hoa | gia | vol 1h | m30 | h6 | mua/ban h1 | tuoi | hang |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for c in rows:
            f.write("| %s | %s | `%s` | `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %.1fh | %s |\n" % (
                g, c["ma"], c["ca"], c.get("pool") or "", c.get("san") or "", c.get("doi_ung") or "?",
                ("$" + format(int(c["res"]), ",")) if c.get("res") else "—",
                ("%.6f" % c["res_q"]) if c.get("res_q") else "—",
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
    """🆕 D4: GOI TUNG CON. Do 18/09: mot cu voi 6 dia chi tra ve 1/6 con, goi tung con tra du 6/6.
    Thieu con nao = GoPlus khong co du lieu con do, KHONG phai sach."""
    ra = {}
    loi = []
    for ca in ca_list:
        ok, j, ly = get_lai("%s?contract_addresses=%s" % (GOPLUS, ca))
        if not ok:
            loi.append("%s=%s" % (ca[:10], ly))
        else:
            for k, v in (j.get("result") or {}).items():
                ra[k.lower()] = v
        time.sleep(GP_GIAN)
    return ra, " · ".join(loi)


def loc_vi_7702(g):
    """🆕 D6 (do 18/09 22:2x, 5/5 con lap lai duoc).
    GoPlus danh `is_contract = 1` cho MOI dia chi co ma tren chuoi. Tu EIP-7702, mot VI NGUOI
    BINH THUONG bat smart account cung co ma: dung 23 byte, dang 0xef0100 + 20 byte dia chi
    uy quyen. May cu bo het nhung vi do khoi phep tinh top10 => TOP10 IN RA THAP HON THAT.
    Do duoc: GSTOCK 2,30% -> 7,55% · GCAT 0xc458 2,93% -> 10,35% · AGI 12,21% -> 16,14%.
    Ham nay goi eth_getCode MOT CU cho ca 10 dia chi, tra ve set dia chi la VI NGUOI 7702.
    Loi RPC => tra ve None, va doc_goplus se in ro la chua loc duoc (KHONG im lang)."""
    if not g:
        return set()
    dc = [(h.get("address") or "").lower() for h in (g.get("holders") or [])[:10]
          if str(h.get("is_contract", "")).strip() == "1"
          and (h.get("address") or "").lower() not in HATANG]
    if not dc:
        return set()
    ok, d, ly = rpc([{"jsonrpc": "2.0", "id": i, "method": "eth_getCode",
                      "params": [a, "latest"]} for i, a in enumerate(dc)])
    if not ok or not isinstance(d, list):
        return None
    ra = set()
    for x in d:
        i = x.get("id")
        ma = (x.get("result") or "")
        if isinstance(i, int) and 0 <= i < len(dc) and ma.startswith("0xef0100"):
            ra.add(dc[i])
    return ra


def doc_goplus(g, vi7702=None):
    """Tra ve (chan?, dong in, vi_to, top10). 🔴 ma dong = CANH BAO, KHONG chan.
    🆕 D6: `vi7702` la set dia chi GoPlus goi la hop dong nhung THUC RA la vi nguoi (EIP-7702).
    None = chua loc duoc (RPC hong) => in canh bao, so top10 la SAN DUOI."""
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
    # vi nguoi = bo ha tang cua lo; 🆕 D6: GIU vi 7702 (0xef0100) vi do la VI NGUOI that
    v7 = vi7702 if isinstance(vi7702, set) else set()
    nguoi = []
    dem7 = 0
    for h in (g.get("holders") or [])[:10]:
        a = (h.get("address") or "").lower()
        if a in HATANG:
            continue
        if str(h.get("is_contract", "")).strip() == "1":
            if a not in v7:
                continue
            dem7 += 1
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
    if vi7702 is None:
        dong += "\n   ⚠️ CHUA LOC DUOC VI EIP-7702 (RPC hong) — top10 tren la SAN DUOI, that co the cao hon"
    elif dem7:
        dong += "\n   🆕 da cong lai %d vi EIP-7702 ma GoPlus goi nham la hop dong (D6)" % dem7
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


def in_thuoc(c, anh, ly_anh=""):
    print("   THUOC A tien vao pool: $%s — hang %s/%s trong ro luot nay (cua: top %d)" % (
        format(int(c["res"]), ","), c.get("hang", "?"), c.get("ro", "?"), TOP_RO))
    print("   pool CUA LO %s (%s) · %d pool cung token%s" % (
        (c.get("pool") or "?")[:18], c.get("san") or "?", c.get("npool", 0),
        (" · bo %d pool bao so vo ly" % c["pool_bo"]) if c.get("pool_bo") else ""))
    print("   DOI UNG: %s @ $%s · res quy ve don vi doi ung: %s" % (
        c.get("doi_ung") or "?", ("%.6g" % c["gia_doi"]) if c.get("gia_doi") else "?",
        ("%.4f" % c["res_q"]) if c.get("res_q") else "⛔ khong quy duoc"))
    if c.get("ngoai"):
        dau = "🔴" if c["ngoai"] > c["res"] else "  "
        print("   %s pool BEN THU BA sau nhat: $%s (%s, %s)%s" % (
            dau, format(int(c["ngoai"]), ","), c.get("ngoai_ten") or "?", c.get("ngoai_san") or "?",
            " — SAU HON pool cua lo, Bean vao tien phai biet minh dang vao pool nao" if c["ngoai"] > c["res"] else ""))
    if not anh:
        print("   THUOC B ⬜ CHUA CO ANH CU co du so — %s" % (ly_anh or "luot dau cua con nay, ghi so de lan sau so"))
        print("   THUOC C ⬜ chua cham duoc")
        return
    cach = (time.time() - anh["gio"]) / 3600.0
    print("   (so voi anh chup cach %.1f gio, CUNG pool %s)" % (cach, (anh.get("pool") or "?")[:18]))
    d_res = (c["res"] / anh["res"] - 1) * 100 if anh["res"] else None
    d_vi = (c["vi"] / anh["vi"] - 1) * 100 if (anh["vi"] and c.get("vi")) else None
    dung_q = (anh.get("res_q") and c.get("res_q") and anh.get("doi") == c.get("doi_ung"))
    if dung_q:
        d_q = (c["res_q"] / anh["res_q"] - 1) * 100
        print("   THUOC B tien con vao : %.4f -> %.4f %s (%+.1f%%) %s" % (
            anh["res_q"], c["res_q"], c.get("doi_ung") or "?", d_q,
            "✅ con vao" if d_q > 0 else "🔴 tien dang ra"))
        print("      (do bang DON VI DOI UNG — mien nhiem voi gia %s; bang USD la %s)" % (
            c.get("doi_ung") or "?", ("%+.1f%%" % d_res) if d_res is not None else "?"))
    else:
        print("   THUOC B tien con vao : $%s -> $%s (%s) %s" % (
            format(int(anh["res"]), ","), format(int(c["res"]), ","),
            ("%+.1f%%" % d_res) if d_res is not None else "?",
            "✅ con vao" if (d_res or 0) > 0 else "🔴 tien dang ra"))
        print("      ⚠️ do bang USD vi anh cu chua co so don vi doi ung — co the nhieu vi gia %s doi" % (c.get("doi_ung") or "doi ung"))
    print("   THUOC C nguoi moi    : %s -> %s vi (%s) %s" % (
        format(int(anh["vi"]), ","), format(int(c["vi"] or 0), ","),
        ("%+.1f%%" % d_vi) if d_vi is not None else "?",
        "✅ co nguoi moi" if (d_vi or 0) > 0 else "🔴 nguoi ta dang bo di"))


def cham_ba_thuoc(c, gan):
    """Tra ve (dat?, ly do). None = chua cham duoc, KHAC False."""
    if c.get("hang") is None or c["hang"] > TOP_RO:
        return False, "THUOC A truot: khong nam trong top %d tien cua ro" % TOP_RO
    anh, ly = chon_anh(gan.get(c["ca"]), c.get("pool"))
    c["anh"] = anh
    c["ly_anh"] = ly
    if not anh:
        return None, ly
    if not anh["res"] or not anh["vi"] or not c.get("vi"):
        return None, "thieu so mot trong hai dau"
    # 🆕 D5: uu tien so bang DON VI DOI UNG. Chi khi anh cu khong co so do moi lui ve do la.
    dung_q = (anh.get("res_q") and c.get("res_q") and anh.get("doi") == c.get("doi_ung"))
    if dung_q:
        b = c["res_q"] > anh["res_q"]
        c["nen_b"] = "don vi doi ung (%s)" % (c.get("doi_ung") or "?")
        d_b = (c["res_q"] / anh["res_q"] - 1) * 100
    else:
        b = c["res"] > anh["res"]
        c["nen_b"] = "⚠️ do bang USD — anh cu chua co so don vi doi ung, co the nhieu vi gia %s doi" % (c.get("doi_ung") or "doi ung")
        d_b = (c["res"] / anh["res"] - 1) * 100
    cc = c["vi"] > anh["vi"]
    if b and cc:
        return True, "tien vao +%.1f%% · vi +%.1f%%" % (
            d_b, (c["vi"] / anh["vi"] - 1) * 100)
    return False, "%s%s" % ("" if b else "tien dang ra ", "" if cc else "nguoi dang bo di")


def main():
    so_da_bao = sys.argv[1] if len(sys.argv) > 1 else None
    da_bao = doc_da_bao(so_da_bao)
    gan = doc_anh_cu()
    gio = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    in_nguong()
    print("\nPHIEU BNB · %s" % gio)
    ds, ly = danh_sach()
    if ly:
        print("⛔ LOI GOI API cua lo: %s — KHONG doc thanh 'khong co con nao'" % ly)
        in_cong()
        print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))
        return
    print("lo tra ve: %d con" % len(ds))
    if not ds:
        print("⛔ LO TRA VE RONG — loi goi hay lo im, KHONG ket luan.")
        in_cong()
        return

    tho, dem = loc_tho(ds)
    print("qua loc tho: %d  (bo: %s)" % (tho and len(tho) or 0,
          " · ".join("%s %d" % (k, v) for k, v in dem.items())))
    if not tho:
        print("KHONG CO GI TRONG DAI")
        print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))
        return

    so_bo(tho)
    ngan = [c for c in tho if c.get("res_tho") is None or c["res_tho"] >= RES_SAN]
    print("loc so bo (pool GT xep dau >= $%s, giu ca con goi hong): %d/%d con di tiep"
          % (format(RES_SAN, ","), len(ngan), len(tho)))
    loi_pool = do_pool(ngan)
    for x in loi_pool:
        print("   ⛔ GT %s — LOI GOI, con nay KHONG duoc do" % x)
    do = [c for c in ngan if c.get("res")]
    for c in ngan:
        if not c.get("res"):
            print("   ⛔ %s: %s" % (c["ma"], c.get("ly_pool") or "khong do duoc"))
    print("do duoc pool cua lo: %d" % len(do))
    do = [c for c in do if c["res"] >= RES_SAN]
    print("con tien trong pool >= $%s: %d" % (format(RES_SAN, ","), len(do)))
    if not do:
        print("da ghi %d dong anh chup vao %s" % (ghi_anh([c for c in ngan if c.get("res")]), SO_ANH))
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
    print("GoPlus: doc duoc %d/%d con" % (len(gp), len(top)))

    for c in top:
        dat, ly_thuoc = cham_ba_thuoc(c, gan)
        print("\n%s  %s   (%s)" % (c["ma"], c["ca"], c.get("ten") or ""))
        print("   von hoa $%s · gia %s · tuoi %.1f gio%s" % (
            format(int(c["mc"] or 0), ","), ("%.10g" % c["gia"]) if c.get("gia") else "⬜ khong co pool nao minh la base",
            c["tuoi"], (" · gia doc o pool %s" % (c["gia_pool"] or "")[:14]) if c.get("gia_pool") else ""))
        print("   doi gia: m30 %s · h1 %s · h6 %s · h24 %s · vol 1h $%s · mua/ban h1 %d/%d" % (
            ("%+.1f%%" % c["m30"]) if c.get("m30") is not None else "?",
            ("%+.1f%%" % c["h1"]) if c.get("h1") is not None else "?",
            ("%+.1f%%" % c["h6"]) if c.get("h6") is not None else "?",
            ("%+.1f%%" % c["h24"]) if c.get("h24") is not None else "?",
            format(int(c.get("vol1") or 0), ","), c.get("mua", 0), c.get("ban", 0)))
        in_thuoc(c, c.get("anh"), c.get("ly_anh", ""))

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
        chan, dong_gp, vi_to, top10 = doc_goplus(gp.get(c["ca"]), loc_vi_7702(gp.get(c["ca"])))
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
            CO_LENH, kh, "" if c.get("phi") is not None else
            " (GT khong khai phi pool — dung PHI_LO %.2f%%/chieu do lo tu khai)" % PHI_LO))
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

    print("\nda ghi %d dong anh chup vao %s" % (ghi_anh([c for c in ngan if c.get("res")]), SO_ANH))
    print("UNG VIEN 3/3: %d · %s" % (len(ung), " ".join(c["ma"] for c in ung) or "—"))
    if not ung:
        print("KHONG CO UNG VIEN MOI")
    print("[%d cu · %.0f giay]" % (CU[0], time.time() - T0))


main()
