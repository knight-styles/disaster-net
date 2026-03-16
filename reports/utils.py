import requests
import math
import concurrent.futures
from django.core.cache import cache

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WORLD_DENSITY = {

    # ── INDIA ──────────────────────────────────────────────────────────────
    "IN": {
        "_urban": 11000, "_rural": 450, "_default": 4500,
        # Maharashtra
        "mumbai": 20700, "pune": 5100, "nagpur": 6800, "nashik": 4200,
        "thane": 11000, "aurangabad": 3800, "solapur": 4500,
        # Delhi / NCR
        "delhi": 11300, "new delhi": 11300, "gurgaon": 3500,
        "gurugram": 3500, "noida": 9800, "faridabad": 6200,
        "ghaziabad": 9100,
        # Karnataka
        "bangalore": 4300, "bengaluru": 4300, "mysore": 3100,
        "hubli": 3500, "mangalore": 2800,
        # Tamil Nadu
        "chennai": 26900, "madras": 26900, "coimbatore": 3200,
        "madurai": 7900, "tiruchirappalli": 4500, "salem": 4100,
        # West Bengal
        "kolkata": 24300, "calcutta": 24300, "howrah": 17000,
        "durgapur": 2900, "asansol": 2600,
        # Telangana / Andhra Pradesh
        "hyderabad": 18200, "secunderabad": 18200, "vizag": 4200,
        "visakhapatnam": 4200, "vijayawada": 5900, "warangal": 4000,
        # Gujarat
        "ahmedabad": 11900, "surat": 14000, "vadodara": 5600,
        "rajkot": 4400, "gandhinagar": 2200,
        # Rajasthan
        "jaipur": 6900, "jodhpur": 3500, "kota": 4100, "udaipur": 2700,
        # Uttar Pradesh
        "lucknow": 6200, "kanpur": 10500, "agra": 5300, "varanasi": 7200,
        "allahabad": 4200, "prayagraj": 4200, "meerut": 9000,
        "ghaziabad": 9100, "bareilly": 4400,
        # Bihar
        "patna": 1800, "gaya": 2100, "muzaffarpur": 2800,
        # Madhya Pradesh
        "indore": 4000, "bhopal": 3700, "jabalpur": 3500,
        "gwalior": 3200,
        # Odisha
        "bhubaneswar": 3200, "cuttack": 5100, "rourkela": 2400,
        "puri": 3800, "berhampur": 3600,
        # Punjab / Haryana
        "ludhiana": 4900, "amritsar": 4400, "chandigarh": 9200,
        "jalandhar": 4200,
        # Kerala
        "kochi": 6300, "cochin": 6300, "thiruvananthapuram": 3200,
        "trivandrum": 3200, "kozhikode": 4100, "calicut": 4100,
        # Assam / Northeast
        "guwahati": 2800, "dispur": 2800,
        # Jharkhand
        "ranchi": 2100, "dhanbad": 5700, "jamshedpur": 3900,
        # Chhattisgarh
        "raipur": 2600, "bhilai": 3100,
        # Himachal / Uttarakhand
        "shimla": 1800, "dehradun": 2400,
        # Goa
        "panaji": 1900, "vasco": 2100,
    },

    # ── CHINA ──────────────────────────────────────────────────────────────
    "CN": {
        "_urban": 7400, "_rural": 120, "_default": 3800,
        "shanghai": 3800, "beijing": 1300, "shenzhen": 6500,
        "guangzhou": 1800, "chongqing": 390, "tianjin": 1400,
        "wuhan": 1000, "chengdu": 1400, "nanjing": 1200,
        "xi'an": 980, "xian": 980, "hangzhou": 700, "harbin": 1500,
        "shenyang": 1300, "qingdao": 900, "jinan": 1100,
        "zhengzhou": 1400, "changsha": 1000, "kunming": 900,
        "suzhou": 1500, "dalian": 1000, "fuzhou": 1000,
        "xiamen": 2600, "hefei": 900, "nanning": 850,
        "urumqi": 480, "lhasa": 200,
    },

    # ── USA ────────────────────────────────────────────────────────────────
    "US": {
        "_urban": 1600, "_rural": 15, "_default": 400,
        "new york": 10900, "los angeles": 3200, "chicago": 4700,
        "houston": 1400, "phoenix": 1200, "philadelphia": 4400,
        "san antonio": 1200, "san diego": 1600, "dallas": 1500,
        "san jose": 2300, "miami": 4700, "seattle": 3200,
        "boston": 5200, "washington": 4200, "denver": 1700,
        "atlanta": 700, "las vegas": 800, "portland": 1900,
        "nashville": 600, "memphis": 900, "louisville": 700,
        "baltimore": 2800, "milwaukee": 2300, "albuquerque": 1100,
        "tucson": 900, "fresno": 1800, "sacramento": 1900,
        "mesa": 1100, "kansas city": 600, "omaha": 1100,
        "cleveland": 1900, "pittsburgh": 2100, "minneapolis": 3000,
        "tulsa": 800, "new orleans": 900, "honolulu": 2300,
        "anchorage": 65,
    },

    # ── UK ─────────────────────────────────────────────────────────────────
    "GB": {
        "_urban": 4000, "_rural": 80, "_default": 700,
        "london": 5700, "birmingham": 4000, "manchester": 4800,
        "glasgow": 3400, "liverpool": 4400, "bristol": 3900,
        "edinburgh": 1800, "leeds": 3200, "sheffield": 3600,
        "nottingham": 4400, "leicester": 4600, "coventry": 3900,
        "bradford": 3600, "cardiff": 2500, "belfast": 2700,
        "newcastle": 3200, "stoke": 2800, "southampton": 4600,
        "portsmouth": 5100, "brighton": 3900, "reading": 3200,
        "oxford": 2800, "cambridge": 3400,
    },

    # ── JAPAN ──────────────────────────────────────────────────────────────
    "JP": {
        "_urban": 6000, "_rural": 100, "_default": 3500,
        "tokyo": 6200, "osaka": 12000, "nagoya": 6900,
        "sapporo": 1800, "fukuoka": 4700, "kyoto": 1800,
        "kobe": 2800, "hiroshima": 1300, "sendai": 1400,
        "kitakyushu": 2100, "chiba": 3600, "sakai": 5400,
        "niigata": 1100, "hamamatsu": 900, "okayama": 1200,
        "sagamihara": 2900, "kumamoto": 1800, "kagoshima": 1400,
        "yokohama": 8500,
    },

    # ── BRAZIL ─────────────────────────────────────────────────────────────
    "BR": {
        "_urban": 3800, "_rural": 25, "_default": 1500,
        "sao paulo": 7400, "rio de janeiro": 5300, "salvador": 3700,
        "fortaleza": 3100, "belo horizonte": 3600, "manaus": 900,
        "curitiba": 4000, "recife": 7400, "porto alegre": 2900,
        "belem": 1600, "goiania": 1700, "guarulhos": 4000,
        "campinas": 1500, "sao luis": 1600, "maceio": 2100,
        "natal": 4300, "teresina": 1900, "campo grande": 1100,
        "joao pessoa": 3300, "florianopolis": 670,
    },

    # ── RUSSIA ─────────────────────────────────────────────────────────────
    "RU": {
        "_urban": 3000, "_rural": 20, "_default": 800,
        "moscow": 4900, "saint petersburg": 3800, "novosibirsk": 3200,
        "yekaterinburg": 2800, "kazan": 2100, "chelyabinsk": 2100,
        "omsk": 1900, "samara": 2200, "rostov": 2400, "ufa": 2000,
        "volgograd": 1400, "perm": 1700, "krasnoyarsk": 1500,
        "voronezh": 1700, "vladivostok": 1200,
    },

    # ── GERMANY ────────────────────────────────────────────────────────────
    "DE": {
        "_urban": 2100, "_rural": 90, "_default": 700,
        "berlin": 4000, "hamburg": 2400, "munich": 4700,
        "cologne": 2700, "frankfurt": 3000, "stuttgart": 2900,
        "dusseldorf": 2800, "dortmund": 2100, "essen": 2700,
        "leipzig": 1900, "bremen": 1600, "dresden": 1700,
        "hannover": 2300, "nuremberg": 2700, "duisburg": 2800,
    },

    # ── FRANCE ─────────────────────────────────────────────────────────────
    "FR": {
        "_urban": 3500, "_rural": 55, "_default": 900,
        "paris": 20000, "lyon": 10000, "marseille": 3500,
        "toulouse": 3700, "nice": 4800, "nantes": 4400,
        "bordeaux": 5000, "lille": 7000, "strasbourg": 3500,
        "rennes": 4200, "reims": 3100, "grenoble": 8600,
        "montpellier": 5000, "toulon": 4800,
    },

    # ── ITALY ──────────────────────────────────────────────────────────────
    "IT": {
        "_urban": 3500, "_rural": 80, "_default": 900,
        "rome": 2200, "milan": 7700, "naples": 8200,
        "turin": 6800, "palermo": 4200, "genoa": 5300,
        "bologna": 2800, "florence": 3700, "bari": 2700,
        "catania": 2400, "venice": 265, "verona": 1100,
        "messina": 2000, "padua": 2000,
    },

    # ── SPAIN ──────────────────────────────────────────────────────────────
    "ES": {
        "_urban": 3200, "_rural": 30, "_default": 700,
        "madrid": 5400, "barcelona": 16000, "valencia": 5600,
        "seville": 4400, "zaragoza": 1300, "bilbao": 8800,
        "malaga": 2200, "murcia": 640, "palma": 2200,
        "las palmas": 4800, "alicante": 2300, "granada": 3500,
    },

    # ── PAKISTAN ───────────────────────────────────────────────────────────
    "PK": {
        "_urban": 9000, "_rural": 300, "_default": 4000,
        "karachi": 24000, "lahore": 6300, "faisalabad": 4000,
        "islamabad": 1800, "rawalpindi": 5000, "peshawar": 5500,
        "multan": 3600, "quetta": 2300, "gujranwala": 4800,
        "sialkot": 3800, "hyderabad": 6000,
    },

    # ── BANGLADESH ─────────────────────────────────────────────────────────
    "BD": {
        "_urban": 44000, "_rural": 900, "_default": 12000,
        "dhaka": 44500, "chittagong": 14000, "sylhet": 3200,
        "rajshahi": 5100, "khulna": 5200, "comilla": 4200,
        "mymensingh": 3800, "gazipur": 12000,
    },

    # ── NIGERIA ────────────────────────────────────────────────────────────
    "NG": {
        "_urban": 5000, "_rural": 200, "_default": 2100,
        "lagos": 14800, "kano": 9000, "ibadan": 3600,
        "abuja": 2800, "port harcourt": 5200, "benin city": 3200,
        "kaduna": 2500, "maiduguri": 2200, "zaria": 3100,
        "aba": 4200, "onitsha": 7200, "enugu": 3000,
    },

    # ── INDONESIA ──────────────────────────────────────────────────────────
    "ID": {
        "_urban": 7000, "_rural": 100, "_default": 2500,
        "jakarta": 15900, "surabaya": 8500, "bandung": 14000,
        "medan": 9200, "semarang": 4800, "makassar": 8000,
        "palembang": 4200, "tangerang": 11000, "depok": 11000,
        "bekasi": 13500, "bogor": 8500, "yogyakarta": 13000,
    },

    # ── MEXICO ─────────────────────────────────────────────────────────────
    "MX": {
        "_urban": 3700, "_rural": 50, "_default": 1500,
        "mexico city": 6000, "guadalajara": 3500, "monterrey": 3200,
        "puebla": 3100, "tijuana": 1800, "leon": 2200,
        "ciudad juarez": 1400, "zapopan": 2000, "nezahualcoyotl": 16000,
        "chihuahua": 1000, "merida": 1800, "cancun": 1400,
    },

    # ── AUSTRALIA ──────────────────────────────────────────────────────────
    "AU": {
        "_urban": 500, "_rural": 1, "_default": 50,
        "sydney": 2000, "melbourne": 1600, "brisbane": 900,
        "perth": 350, "adelaide": 450, "canberra": 450,
        "gold coast": 600, "newcastle": 400, "wollongong": 500,
        "hobart": 350, "darwin": 140,
    },

    # ── CANADA ─────────────────────────────────────────────────────────────
    "CA": {
        "_urban": 900, "_rural": 5, "_default": 100,
        "toronto": 4300, "montreal": 3700, "vancouver": 5500,
        "calgary": 1400, "edmonton": 1200, "ottawa": 950,
        "winnipeg": 1400, "quebec city": 1100, "hamilton": 1800,
        "kitchener": 1400, "london": 1200, "halifax": 750,
    },

    # ── SOUTH AFRICA ───────────────────────────────────────────────────────
    "ZA": {
        "_urban": 2000, "_rural": 40, "_default": 500,
        "johannesburg": 2800, "cape town": 1500, "durban": 1600,
        "pretoria": 1000, "port elizabeth": 700, "bloemfontein": 600,
        "east london": 800, "polokwane": 500, "nelspruit": 400,
    },

    # ── EGYPT ──────────────────────────────────────────────────────────────
    "EG": {
        "_urban": 19000, "_rural": 1400, "_default": 8000,
        "cairo": 19400, "alexandria": 5700, "giza": 15000,
        "shubra el kheima": 30000, "port said": 7500,
        "suez": 5200, "luxor": 1800, "aswan": 1200,
        "mansoura": 9400, "tanta": 11000,
    },

    # ── SOUTH KOREA ────────────────────────────────────────────────────────
    "KR": {
        "_urban": 8500, "_rural": 150, "_default": 5000,
        "seoul": 16000, "busan": 4400, "incheon": 2800,
        "daegu": 2800, "daejeon": 2800, "gwangju": 3000,
        "ulsan": 1100, "suwon": 7300, "changwon": 1900,
        "goyang": 6700, "yongin": 2000,
    },

    # ── TURKEY ─────────────────────────────────────────────────────────────
    "TR": {
        "_urban": 5000, "_rural": 100, "_default": 2000,
        "istanbul": 2900, "ankara": 2200, "izmir": 2200,
        "bursa": 1700, "adana": 1700, "gaziantep": 2600,
        "konya": 900, "antalya": 1000, "mersin": 1200,
        "kayseri": 1200, "eskisehir": 1300, "diyarbakir": 2100,
    },

    # ── IRAN ───────────────────────────────────────────────────────────────
    "IR": {
        "_urban": 6000, "_rural": 80, "_default": 2500,
        "tehran": 11000, "mashhad": 4000, "isfahan": 3200,
        "karaj": 5500, "tabriz": 4800, "shiraz": 3200,
        "qom": 4000, "ahvaz": 3600, "kermanshah": 2600,
    },

    # ── SAUDI ARABIA ───────────────────────────────────────────────────────
    "SA": {
        "_urban": 1500, "_rural": 5, "_default": 700,
        "riyadh": 1600, "jeddah": 2400, "mecca": 1600,
        "medina": 700, "dammam": 1200, "taif": 600,
    },

    # ── UAE ────────────────────────────────────────────────────────────────
    "AE": {
        "_urban": 700, "_rural": 5, "_default": 500,
        "dubai": 700, "abu dhabi": 350, "sharjah": 1500,
        "ajman": 9000, "ras al khaimah": 400,
    },

    # ── SINGAPORE ──────────────────────────────────────────────────────────
    "SG": {"_urban": 8300, "_rural": 8300, "_default": 8300, "singapore": 8300},

    # ── MALAYSIA ───────────────────────────────────────────────────────────
    "MY": {
        "_urban": 4000, "_rural": 80, "_default": 1500,
        "kuala lumpur": 7200, "george town": 7800, "ipoh": 2200,
        "johor bahru": 2600, "petaling jaya": 8800, "subang jaya": 5500,
        "kota kinabalu": 1600, "kuching": 1300,
    },

    # ── THAILAND ───────────────────────────────────────────────────────────
    "TH": {
        "_urban": 5000, "_rural": 120, "_default": 2000,
        "bangkok": 5400, "chiang mai": 3400, "pattaya": 3200,
        "nonthaburi": 6200, "pak kret": 5800, "hat yai": 3100,
    },

    # ── PHILIPPINES ────────────────────────────────────────────────────────
    "PH": {
        "_urban": 9000, "_rural": 200, "_default": 4000,
        "manila": 71000, "quezon city": 17500, "caloocan": 19600,
        "davao": 1700, "cebu": 3800, "zamboanga": 1200,
        "pasig": 19700, "taguig": 12400, "antipolo": 3600,
    },

    # ── VIETNAM ────────────────────────────────────────────────────────────
    "VN": {
        "_urban": 8000, "_rural": 400, "_default": 3500,
        "ho chi minh": 4300, "saigon": 4300, "hanoi": 2300,
        "da nang": 1700, "can tho": 1000, "hai phong": 1400,
        "bien hoa": 3600, "hue": 1200,
    },

    # ── ARGENTINA ──────────────────────────────────────────────────────────
    "AR": {
        "_urban": 3000, "_rural": 20, "_default": 1200,
        "buenos aires": 15000, "cordoba": 3000, "rosario": 3400,
        "mendoza": 2000, "tucuman": 4800, "la plata": 2900,
        "mar del plata": 2000, "salta": 1600,
    },

    # ── COLOMBIA ───────────────────────────────────────────────────────────
    "CO": {
        "_urban": 5000, "_rural": 50, "_default": 2000,
        "bogota": 4700, "medellin": 4700, "cali": 3800,
        "barranquilla": 3600, "cartagena": 3000, "bucaramanga": 3100,
    },

    # ── KENYA ──────────────────────────────────────────────────────────────
    "KE": {
        "_urban": 4500, "_rural": 80, "_default": 1500,
        "nairobi": 4700, "mombasa": 4900, "kisumu": 2200,
        "nakuru": 1800, "eldoret": 1500,
    },

    # ── ETHIOPIA ───────────────────────────────────────────────────────────
    "ET": {
        "_urban": 5000, "_rural": 120, "_default": 1800,
        "addis ababa": 5200, "dire dawa": 2100, "mekelle": 1800,
    },

    # ── GHANA ──────────────────────────────────────────────────────────────
    "GH": {
        "_urban": 4000, "_rural": 100, "_default": 1200,
        "accra": 4900, "kumasi": 3400, "tamale": 1800,
    },

    # ── NETHERLANDS ────────────────────────────────────────────────────────
    "NL": {
        "_urban": 4500, "_rural": 200, "_default": 1500,
        "amsterdam": 5100, "rotterdam": 3100, "the hague": 3400,
        "utrecht": 3400, "eindhoven": 2600,
    },

    # ── PORTUGAL ───────────────────────────────────────────────────────────
    "PT": {
        "_urban": 3000, "_rural": 50, "_default": 800,
        "lisbon": 5400, "porto": 5800, "braga": 1700,
        "setubal": 1600, "coimbra": 1400,
    },

    # ── SWEDEN ─────────────────────────────────────────────────────────────
    "SE": {
        "_urban": 1200, "_rural": 15, "_default": 200,
        "stockholm": 4800, "gothenburg": 1400, "malmo": 2100,
        "uppsala": 1400, "vasteras": 1000,
    },

    # ── NORWAY ─────────────────────────────────────────────────────────────
    "NO": {
        "_urban": 1000, "_rural": 10, "_default": 150,
        "oslo": 1600, "bergen": 900, "trondheim": 800,
    },

    # ── SWITZERLAND ────────────────────────────────────────────────────────
    "CH": {
        "_urban": 2500, "_rural": 100, "_default": 800,
        "zurich": 4600, "geneva": 12100, "basel": 5100,
        "bern": 2600, "lausanne": 3200,
    },

    # ── POLAND ─────────────────────────────────────────────────────────────
    "PL": {
        "_urban": 2000, "_rural": 50, "_default": 700,
        "warsaw": 3400, "krakow": 2400, "lodz": 2700,
        "wroclaw": 2200, "poznan": 2000, "gdansk": 1800,
    },

    # ── UKRAINE ────────────────────────────────────────────────────────────
    "UA": {
        "_urban": 3000, "_rural": 40, "_default": 900,
        "kyiv": 3500, "kharkiv": 3000, "odessa": 2500,
        "dnipro": 2200, "donetsk": 4500, "zaporizhzhia": 2000,
    },

    # ── NEW ZEALAND ────────────────────────────────────────────────────────
    "NZ": {
        "_urban": 500, "_rural": 5, "_default": 60,
        "auckland": 1100, "wellington": 1500, "christchurch": 500,
        "hamilton": 600, "tauranga": 500,
    },

    # ── GLOBAL FALLBACK ────────────────────────────────────────────────────
    "_WORLD": {"_urban": 3000, "_rural": 100, "_default": 1500},
}


def lookup_density(country_code, city_name, place_type="city"):
    """
    Returns people/km² for a given country + city combination.
    Falls back gracefully: city match → urban/rural avg → country default → world default.
    """
    country_code = (country_code or "").upper()
    city_name    = (city_name or "").lower().strip()
    table        = WORLD_DENSITY.get(country_code, WORLD_DENSITY["_WORLD"])

    if city_name:
        for key, density in table.items():
            if key.startswith("_"):
                continue
            if key in city_name or city_name in key:
                return density

    if place_type in ("city", "town"):
        return table.get("_urban", table.get("_default", 1500))
    elif place_type == "village":
        return table.get("_rural", table.get("_default", 400))
    else:
        return table.get("_default", 1500)


def estimate_from_density(lat, lng, radius_km=1):
    """
    Fast density-table crowd estimate.
    Single Nominatim call (cached 24h) → table lookup → π·r² math.
    No external API keys needed. Works globally.
    """
    cache_key = f"density_est_{round(lat, 3)}_{round(lng, 3)}_{radius_km}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    country_code = ""
    city_name    = ""
    place_type   = "city"

    try:
        r = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}",
            headers={"User-Agent": "disaster-management-app"},
            timeout=8
        )
        r.raise_for_status()
        addr = r.json().get("address", {})

        country_code = addr.get("country_code", "").upper()
        city_name    = (
            addr.get("city") or addr.get("town") or
            addr.get("village") or addr.get("county") or ""
        ).lower()

        if   addr.get("city"):    place_type = "city"
        elif addr.get("town"):    place_type = "town"
        elif addr.get("village"): place_type = "village"
        else:                     place_type = "rural"

    except Exception as e:
        print(f"Reverse geocode error: {e}")

    density   = lookup_density(country_code, city_name, place_type)
    area_km2  = math.pi * (radius_km ** 2)
    estimated = int(density * area_km2)

    print(f"Density [{lat:.4f},{lng:.4f}] {country_code}/{city_name} {place_type} {density}/km² r={radius_km}km → {estimated:,}")

    result = (estimated, city_name.title(), country_code)
    cache.set(cache_key, result, timeout=86400)
    return result


def estimate_crowd_osm(lat, lng, radius_m=1000):
    cache_key = f"osm_{round(lat, 4)}_{round(lng, 4)}_{radius_m}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    amenity_q  = f"[out:json][timeout:12];\nnode[\"amenity\"](around:{radius_m},{lat},{lng});\nout count;"
    building_q = f"[out:json][timeout:12];\nway[\"building\"](around:{radius_m},{lat},{lng});\nout count;"

    amenity_count = building_count = 0

    try:
        r1  = requests.post(OVERPASS_URL, data=amenity_q, timeout=12)
        els = r1.json().get("elements", [])
        amenity_count = int(els[0].get("tags", {}).get("total", 0)) if els else 0
    except Exception as e:
        print(f"OSM amenity error: {e}")

    try:
        r2  = requests.post(OVERPASS_URL, data=building_q, timeout=12)
        els = r2.json().get("elements", [])
        building_count = int(els[0].get("tags", {}).get("total", 0)) if els else 0
    except Exception as e:
        print(f"OSM building error: {e}")

    radius_km = radius_m / 1000
    ppf       = 12 if radius_km <= 1 else 18 if radius_km <= 2 else 25 if radius_km <= 5 else 35
    estimated = (amenity_count + building_count) * ppf

    print(f"OSM [{lat:.4f},{lng:.4f}] r={radius_m}m amenities={amenity_count} buildings={building_count} → {estimated:,}")

    if estimated > 0:
        cache.set(cache_key, estimated, timeout=3600)
    return estimated


def crowd_level(count):
    if count < 100:
        return "Minimal"
    elif count < 2000:
        return "Low"
    elif count < 10000:
        return "Moderate"
    elif count < 50000:
        return "High"
    else:
        return "Critical"


def reverse_geocode(lat, lng):
    cache_key = f"geocode_{round(lat, 4)}_{round(lng, 4)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        r    = requests.get(
            f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}",
            headers={"User-Agent": "disaster-management-app"}, timeout=8
        )
        addr  = r.json().get("address", {})
        state = addr.get("state")
        city  = addr.get("city") or addr.get("town") or addr.get("village")
        result = (state, city)
        cache.set(cache_key, result, timeout=86400)
        return result
    except Exception as e:
        print(f"Reverse geocode error: {e}")
        return (None, None)


def geocode_address(address):
    cache_key = f"geocode_addr_{address.lower().strip()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "disaster-management-app"}, timeout=8
        )
        results = r.json()
        if results:
            result = (float(results[0]["lat"]), float(results[0]["lon"]))
            cache.set(cache_key, result, timeout=86400)
            return result
    except Exception as e:
        print(f"Geocode address error: {e}")
    return (None, None)


def get_crowd_for_location(lat, lng, radius=1):
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        density_future = ex.submit(estimate_from_density, lat, lng, radius)
        osm_future     = ex.submit(estimate_crowd_osm, lat, lng, radius * 1000)

    density_est, city_name, country = density_future.result()
    osm_est                         = osm_future.result()

    print(f"FINAL [{lat:.4f},{lng:.4f}] r={radius}km | density={density_est:,} osm={osm_est:,}")

    if density_est > 0 and osm_est > 0:
        total = int(density_est * 0.7 + osm_est * 0.3)
    elif density_est > 0:
        total = density_est
    elif osm_est > 0:
        total = osm_est
    else:
        total = 0

    return total, crowd_level(total)