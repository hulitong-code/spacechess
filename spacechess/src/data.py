# data.py - 星际征途探索强手棋 游戏数据
# 所有数据直接从原版 Scratch 项目提取
# 星球描述和实验类型由 星球数据.md 维护，程序启动时自动读取

import re as _re, os as _os

# ─────────────────────────────
# 棋盘格子 (32格，索引0=格1=地球)
# ─────────────────────────────
BOARD = [
    {"name": "地球",           "name_en": "Earth",             "type": "start"},
    {"name": "金星",           "name_en": "Venus",             "type": "planet", "planet_id": 1},
    {"name": "水星",           "name_en": "Mercury",           "type": "planet", "planet_id": 2},
    {"name": "事件卡",         "name_en": "Event Card",        "type": "event"},
    {"name": "坦普尔一号彗星", "name_en": "Temple 1 Comet",   "type": "planet", "planet_id": 3},
    {"name": "格利泽581g",     "name_en": "Gliese 581g",       "type": "planet", "planet_id": 4},
    {"name": "哈雷彗星",       "name_en": "Halley's Comet",    "type": "planet", "planet_id": 5},
    {"name": "比邻星",         "name_en": "Proxima Centauri",  "type": "planet", "planet_id": 6},
    {"name": "宜居带",         "name_en": "Habitable Zone",    "type": "safe"},
    {"name": "补给站",         "name_en": "Supply Depot",      "type": "bonus",  "amount": -20},
    {"name": "遭遇太空垃圾",   "name_en": "Space Debris",      "type": "penalty","amount": -50},
    {"name": "冥王星",         "name_en": "Pluto",             "type": "planet", "planet_id": 7},
    {"name": "天狼星",         "name_en": "Sirius",            "type": "planet", "planet_id": 8},
    {"name": "机会卡",         "name_en": "Chance Card",       "type": "chance"},
    {"name": "海王星",         "name_en": "Neptune",           "type": "planet", "planet_id": 9},
    {"name": "天王星",         "name_en": "Uranus",            "type": "planet", "planet_id": 10},
    {"name": "空间站",         "name_en": "Space Station",     "type": "jail"},
    {"name": "定时检查",       "name_en": "Routine Check",     "type": "penalty","amount": -20},
    {"name": "土卫六",         "name_en": "Titan",             "type": "planet", "planet_id": 11},
    {"name": "土卫二",         "name_en": "Enceladus",         "type": "planet", "planet_id": 12},
    {"name": "土星",           "name_en": "Saturn",            "type": "planet", "planet_id": 13},
    {"name": "事件卡",         "name_en": "Event Card",        "type": "event"},
    {"name": "木卫二",         "name_en": "Europa",            "type": "planet", "planet_id": 14},
    {"name": "木星",           "name_en": "Jupiter",           "type": "planet", "planet_id": 15},
    {"name": "太空实验室",     "name_en": "Space Lab",         "type": "lab"},
    {"name": "补给站",         "name_en": "Supply Depot",      "type": "bonus",  "amount": 20},
    {"name": "艳后星",         "name_en": "Cleopatra",         "type": "planet", "planet_id": 16},
    {"name": "谷神星",         "name_en": "Ceres",             "type": "planet", "planet_id": 17},
    {"name": "机会卡",         "name_en": "Chance Card",       "type": "chance"},
    {"name": "定时检修",       "name_en": "Maint. Check",      "type": "penalty","amount": -20},
    {"name": "火星",           "name_en": "Mars",              "type": "planet", "planet_id": 18},
    {"name": "月球",           "name_en": "Moon",              "type": "planet", "planet_id": 19},
]

# ─────────────────────────────
# 星球数据
# 每颗星球有 4 个升级级别（0=初始，3=最高）
# explore  = 探索费用（购买或升级到该级的花费）
# toll     = 通行费用（对方经过时收取）
# ─────────────────────────────
# 星球数据（desc / experiments / levels 由 星球数据.md 加载）
# ─────────────────────────────
_EMPTY_LV = {"explore": 0, "toll": 0, "trade": 0, "mortgage": 0}

PLANETS = {pid: {"name": name,
                 "name_en": "",
                 "desc": "",
                 "desc_en": "",
                 "facts": [],
                 "facts_en": [],
                 "experiments": [False, False, False],
                 "levels": [dict(_EMPTY_LV) for _ in range(4)]}
           for pid, name in {
               1: "金星",        2: "水星",        3: "坦普尔一号彗星",
               4: "格利泽581g",  5: "哈雷彗星",    6: "比邻星",
               7: "冥王星",      8: "天狼星",       9: "海王星",
               10: "天王星",     11: "土卫六",      12: "土卫二",
               13: "土星",       14: "木卫二",      15: "木星",
               16: "艳后星",     17: "谷神星",      18: "火星",
               19: "月球",
           }.items()}

# ─────────────────────────────
# 从 星球数据.md 加载所有星球信息
# ─────────────────────────────
_LV_NAME_MAP = {"观测": 0, "卫星探测": 1, "着陆车探测": 2, "成功探索": 3}

def _parse_num(s):
    s = s.strip()
    if s in ("—", "无", ""):
        return 0
    if s == "不可":
        return -1
    try:
        return int(s)
    except ValueError:
        return 0

def _load_planet_md():
    path = _os.path.join(_os.path.dirname(__file__), "..", "data", "星球信息.md")
    if not _os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()

    for m in _re.finditer(
        r'^## .+?\(ID\s+(\d+)\)(.*?)(?=^## |\Z)',
        text, _re.MULTILINE | _re.DOTALL
    ):
        pid  = int(m.group(1))
        body = m.group(2)
        if pid not in PLANETS:
            continue

        # ── 实验类型（表格形式）──
        lines = body.splitlines()
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("|") and "采集矿物" in s and "水实验" in s and "植物实验" in s:
                for j in range(i + 1, min(i + 4, len(lines))):
                    s2 = lines[j].strip()
                    if not s2.startswith("|"):
                        break
                    c2 = [c.strip() for c in s2.split("|")[1:-1]]
                    if len(c2) == 3 and not all(c.replace("-", "").replace(":", "") == "" for c in c2):
                        PLANETS[pid]["experiments"] = [c2[0] == "是", c2[1] == "是", c2[2] == "是"]
                        break
                break

        # ── 费用表（单张5列：等级 | 探索费 | 过路费 | 收购费 | 交公价）──
        levels = [dict(_EMPTY_LV) for _ in range(4)]
        for line in body.splitlines():
            s = line.strip()
            if not s.startswith("|") or not s.endswith("|"):
                continue
            cells = [c.strip() for c in s.split("|")[1:-1]]
            if len(cells) < 5 or cells[0] not in _LV_NAME_MAP:
                continue
            idx = _LV_NAME_MAP[cells[0]]
            levels[idx] = {
                "explore":  _parse_num(cells[1]),
                "toll":     _parse_num(cells[2]),
                "trade":    _parse_num(cells[3]),
                "mortgage": _parse_num(cells[4]),
            }
        PLANETS[pid]["levels"] = levels

        # ── 趣味知识 ──
        facts = []
        in_facts = False
        for line in body.splitlines():
            s = line.strip()
            if s == "### 趣味知识":
                in_facts = True
                continue
            if in_facts:
                if s.startswith("### "):
                    break
                if s.startswith("- "):
                    facts.append(s[2:].strip())
        PLANETS[pid]["facts"] = facts

        # ── 描述文字（只取第一个 ### 之前的纯文本行）──
        desc_lines = []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith("### "):
                break
            if not s or s.startswith("|") or s.startswith("**") \
                     or s.startswith("---") or s.startswith("#"):
                continue
            desc_lines.append(s)
        if desc_lines:
            PLANETS[pid]["desc"] = "".join(desc_lines)

_load_planet_md()

# ─────────────────────────────
# 英文星球数据
# ─────────────────────────────
_PLANET_EN = {
    1: {
        "name_en": "Venus",
        "desc_en": "Venus is the second planet from the Sun and is similar in size and mass to Earth. Its thick sulfuric acid clouds and carbon dioxide atmosphere push surface temperatures to 460°C — the hottest planet in the solar system.",
        "facts_en": [
            "Venus is the hottest planet in the Solar System with surface temperatures reaching 460°C — hotter even than Mercury!",
            "Venus rotates opposite to most planets, so the Sun rises in the west on Venus.",
            "A day on Venus is longer than a year — it takes 243 Earth days to rotate but only 225 days to orbit the Sun!",
        ],
    },
    2: {
        "name_en": "Mercury",
        "desc_en": "Mercury is the closest planet to the Sun and the smallest of the eight planets. Its surface is covered with craters and it has no atmosphere or natural satellites.",
        "facts_en": [
            "Mercury has no atmosphere to retain heat — daytime reaches 430°C while nights drop to -180°C, a swing of over 600 degrees!",
            "Mercury is the fastest planet around the Sun, completing one orbit in just 88 days — so a Mercury year is only 88 days!",
            "Despite its small size, Mercury's iron core makes up about 83% of its radius.",
        ],
    },
    3: {
        "name_en": "Temple 1 Comet",
        "desc_en": "Temple 1 is a periodic comet too faint to see with the naked eye. NASA's Deep Impact probe struck its nucleus, and the data revealed primitive materials from the early Solar System inside the comet.",
        "facts_en": [
            "In 2005, NASA's Deep Impact spacecraft fired a copper projectile into this comet — like shooting a cannonball in space!",
            "A comet's tail always points away from the Sun, so when a comet moves backward its tail is actually in front!",
            "Scientists have found amino acids inside comets — one of the basic building blocks of life!",
        ],
    },
    4: {
        "name_en": "Gliese 581g",
        "desc_en": "Gliese 581g orbits the red dwarf star Gliese 581 in Libra, about 20.5 light-years from Earth. It may be the most Earth-like exoplanet discovered so far.",
        "facts_en": [
            "Gliese 581g is about 20.5 light-years away — even at the speed of light it would take 20 years to reach!",
            "It sits in its star's habitable zone where temperatures may allow liquid water to exist — possibly supporting life!",
            "Its parent star Gliese 581 is a red dwarf much smaller than the Sun, yet with a lifespan many times longer.",
        ],
    },
    5: {
        "name_en": "Halley's Comet",
        "desc_en": "Halley's Comet is the only short-period comet visible from Earth with the naked eye. It appears roughly every 76 years and is the first periodic comet ever recorded by humans.",
        "facts_en": [
            "Halley's Comet returns about every 76 years — a person might see it at most twice in a lifetime!",
            "Ancient Chinese astronomers recorded Halley's Comet as early as 240 BC — one of the world's earliest observations.",
            "Each time it nears the Sun, Halley's Comet evaporates and shrinks, losing millions of tons of material per pass.",
        ],
    },
    6: {
        "name_en": "Proxima Centauri",
        "desc_en": "Proxima Centauri, located in the constellation Centaurus, is the nearest star to our Sun.",
        "facts_en": [
            "Proxima Centauri is the closest star to Earth besides the Sun, yet it is still 4.24 light-years away — light takes over 4 years!",
            "It is a red dwarf with only 1/600 the brightness of the Sun — completely invisible to the naked eye.",
            "In 2016, scientists discovered a planet 'Proxima b' nearby, possibly in the habitable zone and perhaps suitable for life!",
        ],
    },
    7: {
        "name_en": "Pluto",
        "desc_en": "Pluto is a deeply frozen world where even summer temperatures reach only -230°C. In 2006, it was reclassified as a dwarf planet.",
        "facts_en": [
            "In 2006, Pluto was 'demoted' from the 9th planet to a dwarf planet — a controversial change many people still debate!",
            "NASA's New Horizons probe photographed a large heart-shaped region on Pluto, affectionately called 'Pluto's Heart'.",
            "Pluto's largest moon Charon is nearly as big as Pluto itself — they orbit each other like a binary system.",
        ],
    },
    8: {
        "name_en": "Sirius",
        "desc_en": "Sirius is the brightest star in the night sky. What appears as a single star is actually a binary star system.",
        "facts_en": [
            "Sirius is the brightest star in the night sky, with a luminosity more than 25 times that of the Sun!",
            "Sirius is actually a 'double star' system: the main star Sirius A, and a white dwarf companion Sirius B.",
            "Ancient Egyptians used the rising of Sirius as a signal for the Nile flood — critical for agriculture.",
        ],
    },
    9: {
        "name_en": "Neptune",
        "desc_en": "Neptune is the eighth and farthest known planet from the Sun. It receives very little sunlight and is one of the coldest regions in the solar system. Neptune has the strongest winds in the solar system — up to 2,100 km/h.",
        "facts_en": [
            "Neptune is the only planet whose position was predicted mathematically before it was found with a telescope!",
            "Neptune was discovered in 1846 and only completed its first full orbit in 2011 — one Neptune year equals 165 Earth years!",
            "Wind speeds on Neptune reach 2,100 km/h — several times stronger than the most powerful hurricanes on Earth!",
        ],
    },
    10: {
        "name_en": "Uranus",
        "desc_en": "Uranus is the third-largest planet in the solar system and seventh from the Sun. It appears blue-green and was the first planet discovered using a telescope.",
        "facts_en": [
            "Uranus rotates almost on its side with an axial tilt of ~98°, rolling around the Sun like a ball on the ground!",
            "Uranus is the coldest planet in the solar system, reaching -224°C — even colder than the more distant Neptune!",
            "Uranus was the first planet discovered with a telescope, found in 1781 — before that, Saturn was thought to be the outermost planet.",
        ],
    },
    11: {
        "name_en": "Titan",
        "desc_en": "Titan is Saturn's largest and most unique moon, with a dense atmosphere similar to the early Earth when life was just beginning.",
        "facts_en": [
            "Titan is the only moon in the solar system with a thick atmosphere — denser than Earth's!",
            "Titan has lakes and rivers on its surface, but instead of water they are filled with liquid methane — natural gas!",
            "Scientists think Titan's atmosphere resembles early Earth, and some form of primitive life might exist there.",
        ],
    },
    12: {
        "name_en": "Enceladus",
        "desc_en": "Enceladus is Saturn's sixth-largest moon. Probes discovered geysers at its south pole, making it one of the best candidates in the search for extraterrestrial life.",
        "facts_en": [
            "Enceladus is covered in ice and reflects nearly all sunlight — making it one of the brightest bodies in the solar system.",
            "Its south pole has massive geysers that shoot water vapor and ice particles hundreds of kilometers into space!",
            "Scientists found organic molecules in the water vapor expelled by Enceladus — a major clue in the search for alien life!",
        ],
    },
    13: {
        "name_en": "Saturn",
        "desc_en": "Saturn, second in size only to Jupiter, is the solar system's second-largest planet. Its surface, like Jupiter's, is almost entirely gas. A Saturnian day is about 10.6 hours.",
        "facts_en": [
            "Saturn's density is so low that if you had a big enough bathtub, Saturn would float in water!",
            "Saturn has the most spectacular ring system in the solar system, made of countless ice chunks and rocks over 270,000 km wide.",
            "Saturn has 146 known moons — the most of any planet in the solar system!",
        ],
    },
    14: {
        "name_en": "Europa",
        "desc_en": "Europa is Jupiter's fourth-largest moon, discovered by Galileo in 1610. Scientists believe that conditions suitable for life may exist beneath its icy surface.",
        "facts_en": [
            "Beneath Europa's ice shell there may be a vast liquid water ocean more than 100 km deep!",
            "Scientists consider Europa one of the most likely places to find extraterrestrial life in the solar system.",
            "Europa's icy surface is covered with cracks — like Earth's tectonic plates — caused by Jupiter's gravity.",
        ],
    },
    15: {
        "name_en": "Jupiter",
        "desc_en": "Jupiter is the largest planet in the solar system — about 1,300 Earths could fit inside it. It is one of the brightest planets, second only to the Moon and Venus.",
        "facts_en": [
            "Jupiter's Great Red Spot is a super-storm that has lasted at least 300 years — and it's larger than the entire Earth!",
            "Jupiter has 95 known moons; the largest four are visible with an ordinary telescope.",
            "Jupiter acts like a 'space shield' — its powerful gravity attracts comets and asteroids, protecting Earth from impacts!",
        ],
    },
    16: {
        "name_en": "Cleopatra",
        "desc_en": "The 216th asteroid discovered, Cleopatra lies in the asteroid belt between Mars and Jupiter and is shaped like a bone.",
        "facts_en": [
            "Cleopatra is shaped like a dog bone about 270 km long — one of the rarest dumbbell-shaped asteroids!",
            "The asteroid is named after the famous ancient Egyptian queen Cleopatra.",
            "Cleopatra is primarily composed of metallic iron and nickel, containing mineral resources of incalculable value!",
        ],
    },
    17: {
        "name_en": "Ceres",
        "desc_en": "Ceres lies in the asteroid belt between Mars and Jupiter — the largest known body in the main belt. It was reclassified as a dwarf planet in 2006. Research confirms large amounts of ice inside.",
        "facts_en": [
            "Ceres is the largest body in the asteroid belt, accounting for about one-third of the belt's total mass!",
            "NASA's Dawn probe discovered mysterious bright spots on Ceres — found to be salt crystals left behind by evaporating brine!",
            "Ceres was discovered in 1801 as a planet, later downgraded to an asteroid, then upgraded to a dwarf planet in 2006.",
        ],
    },
    18: {
        "name_en": "Mars",
        "desc_en": "A Martian day is slightly longer than 24 hours, and Mars has seasons similar to Earth's. Its reddish color comes from iron-rich rocks that have oxidized (rusted).",
        "facts_en": [
            "Mars has the tallest mountain in the solar system — Olympus Mons at ~21.9 km, 2.5 times taller than Mount Everest!",
            "Mars is red because its surface rocks and soil are rich in iron oxide — basically rust!",
            "Over 50 probes have been sent to Mars — it is the most studied planet beyond Earth.",
        ],
    },
    19: {
        "name_en": "Moon",
        "desc_en": "The Moon is the closest celestial body to Earth and Earth's only natural satellite. It was humanity's first destination in space exploration.",
        "facts_en": [
            "In 1969, Apollo 11 astronaut Neil Armstrong became the first human to walk on a body beyond Earth!",
            "The Moon has no atmosphere, so footprints left by astronauts can last for millions of years without eroding.",
            "The Moon is slowly drifting away from Earth at about 3.8 cm per year.",
        ],
    },
}

# 合并英文星球数据
for _pid, _en in _PLANET_EN.items():
    if _pid in PLANETS:
        PLANETS[_pid].update(_en)

# 哪个格子对应哪颗星球（格子索引0-31 → planet_id, 0=非星球格）
CELL_PLANET_ID = [0,1,2,0,3,4,5,6,0,0,0,7,8,0,9,10,0,0,11,12,13,0,14,15,0,0,16,17,0,0,18,19]

# ─────────────────────────────
# 卡牌效果定义
# action 字段说明：
#   "fund"             - 资金变化 (amount)
#   "teleport"         - 传送到指定格（cell, 0-indexed）
#   "reverse"          - 下一轮反向移动
#   "move"             - 立即额外移动 (steps, 负数=反向, "reverse"=退回本次步数)
#   "jail"             - 进入空间站（停一轮）
#   "skip_turn"        - 原地停走一轮（不去空间站）
#   "extra_roll"       - 本轮可再投一次骰子
#   "draw_chance"      - 再抽一张机会卡
#   "keep"             - 保留此卡，随时使用（免一次过路费）
#   "lab"              - 传送到太空实验室并可做实验
#   "swap_planet"      - 与其他玩家互换一颗星球
#   "reset"            - 返回地球，经费重置为起始金额
#   "comet_jail"       - 所有持有彗星星球的玩家停走一轮
#   "give_fund"        - 支付 amount 经费给指定玩家（amount为负数）
#   "none"             - 无效果
# ─────────────────────────────
EVENT_CARDS = [
    {"id":  1, "name": "疑有黑洞",       "desc": "有恒星围绕着不可见的东西旋转，那里可能是黑洞，为了安全下一轮投掷骰子反向行走。",
     "name_en": "Suspected Black Hole",
     "desc_en": "A star seems to orbit something invisible — possibly a black hole. For safety, your next roll moves you backward.",
     "action": "reverse"},
    {"id":  2, "name": "去往火星",       "desc": "好奇号火星车发来最新资料中有新发现，请探索者前往火星侦察。",
     "name_en": "Head to Mars",
     "desc_en": "The Curiosity rover has new findings on Mars! You're dispatched to investigate. Move to Mars.",
     "action": "teleport", "cell": 30},
    {"id":  3, "name": "调配探索者",     "desc": "为了更有效率地帮助地球获得数据，可按照你的想法调配其他玩家的位置，可移动三次。",
     "name_en": "Reposition Explorers",
     "desc_en": "To gather data more efficiently for Earth, you may reposition other explorers up to 3 times.",
     "action": "reposition"},
    {"id":  4, "name": "原路返回",       "desc": "你所在的星球出现严重风暴，需立即撤离，退回到本次出发点。",
     "name_en": "Retreat!",
     "desc_en": "A severe storm has struck your planet. Evacuate immediately and return to your starting position this turn.",
     "action": "move", "steps": "reverse"},
    {"id":  5, "name": "互换星球",       "desc": "选择一名玩家，与其互换一颗星球。",
     "name_en": "Planet Swap",
     "desc_en": "Choose a player and swap one planet each.",
     "action": "swap_planet"},
    {"id":  6, "name": "前往太空实验室", "desc": "采集到新资源，前往太空实验室进行试验。",
     "name_en": "Visit Space Lab",
     "desc_en": "You've collected new resources! Head to the Space Lab to conduct experiments.",
     "action": "lab"},
    {"id":  7, "name": "前往国际空间站", "desc": "前往空间站，将旅途中获得的信息发送给地球，为地球的未来做出贡献。",
     "name_en": "Visit Space Station",
     "desc_en": "Report your findings to Earth via the Space Station. Go to the Space Station and skip a turn.",
     "action": "jail"},
    {"id":  8, "name": "暂停一轮",       "desc": "定时向地球传回近期收获的数据，下轮暂停。",
     "name_en": "Skip a Turn",
     "desc_en": "Time to transmit your recent data back to Earth. Skip your next turn.",
     "action": "skip_turn"},
    {"id":  9, "name": "彗星失联",       "desc": "由于彗星运动，与探测器失联。所有拥有彗星星球的玩家停走一轮。",
     "name_en": "Comet Blackout",
     "desc_en": "A comet's movement has disrupted communications with the probe. All players who own a comet planet skip a turn.",
     "action": "comet_jail"},
    {"id": 10, "name": "重新出发",       "desc": "警告！飞行器出现严重故障无法继续探索，需立即返回地球，手中费用变为起始金额。",
     "name_en": "Back to Earth",
     "desc_en": "Warning! Your spacecraft has suffered critical failure. Return to Earth immediately. Your funds reset to the starting amount.",
     "action": "reset"},
    {"id": 11, "name": "抽取机会卡",     "desc": "有一位善良的探索者和你分享了信息，从机会卡底部抽取一张卡。",
     "name_en": "Draw Chance Card",
     "desc_en": "A kind explorer shared useful information with you. Draw a Chance card from the bottom of the deck.",
     "action": "draw_chance"},
    {"id": 12, "name": "一次机会",       "desc": "二选一：再投掷一次骰子，或者抽一张机会卡。",
     "name_en": "Lucky Chance",
     "desc_en": "Choose one: roll the dice again, or draw a Chance card.",
     "action": "extra_roll"},  # 暂简化为再投骰子
    {"id": 13, "name": "求救",           "desc": "联络设备发出微弱信号，可联络其他探索者，被求救者必须给予帮助。保留此卡随时使用。",
     "name_en": "SOS",
     "desc_en": "Your signal is faint but readable. Another explorer must help you. Keep this card — use it anytime to skip a toll.",
     "action": "keep"},
    {"id": 14, "name": "意外惊喜",       "desc": "意外获得一台探测器，探测器内有许多未知信息，让旅途更加顺利，向前走五步。",
     "name_en": "Surprise Find!",
     "desc_en": "You unexpectedly found a probe packed with valuable data. Great news for your journey! Move forward 5 spaces.",
     "action": "move", "steps": 5},
]

# 彗星星球 planet_id 列表（用于 comet_jail）
COMET_PLANET_IDS = {3, 5}   # 坦普尔一号彗星=3，哈雷彗星=5

CHANCE_CARDS = [
    {"id":  1, "name": "有新的发现",       "desc": "穷极想象得到的结果，可能离真相十万八千里。后退5步。",
     "name_en": "New Discovery?",
     "desc_en": "Imagination can be wild — and so can your conclusions. You may be far from the truth. Move back 5 spaces.",
     "action": "move", "steps": -5},
    {"id":  2, "name": "战胜恐惧和孤独",   "desc": "茫茫宇宙中征途靠自己，战胜孤独和恐惧需要强大的心理。再一次投掷骰子。",
     "name_en": "Conquer Fear",
     "desc_en": "In the vast universe, you must rely on yourself to overcome fear and loneliness. Roll the dice again!",
     "action": "extra_roll"},
    {"id":  3, "name": "不要担心犯错",     "desc": "在犯错之后才能找到正确的道路。回到起点（地球）。",
     "name_en": "Don't Fear Mistakes",
     "desc_en": "Only through mistakes can you find the right path. Return to Earth (Start).",
     "action": "teleport", "cell": 0},
    {"id":  4, "name": "地球人在呼叫你",   "desc": "每个探索者的使命是探索发现地外文明。请任意探索一个未被探索的星球。",
     "name_en": "Earth is Calling!",
     "desc_en": "Every explorer's mission is to discover extraterrestrial life. Freely explore any one unclaimed planet.",
     "action": "explore_free"},
    {"id":  5, "name": "每日健身时间",     "desc": "在太空失重环境下，宇航员必须每天锻炼以维持身体机能。损失10经费。",
     "name_en": "Daily Exercise",
     "desc_en": "In microgravity, astronauts must exercise every day to maintain their health. Lose 10 funds.",
     "action": "fund", "amount": -10},
    {"id":  6, "name": "分享财富",         "desc": "分享，让旅途更加顺利。给任意一名玩家30经费（自己支出30经费）。",
     "name_en": "Share the Wealth",
     "desc_en": "Sharing makes the journey smoother for everyone. Give any player 30 funds (you pay 30 funds).",
     "action": "give_fund", "amount": -30},
    {"id":  7, "name": "前往太空实验室",   "desc": "探索过程中，科学实验可以帮助人类了解更多信息。",
     "name_en": "Visit Space Lab",
     "desc_en": "Scientific experiments during exploration help humanity learn more about the cosmos.",
     "action": "lab"},
    {"id":  8, "name": "获得奖励",         "desc": "你的努力受到认可，获得一笔奖励。你的每一小步，都是迈向成功的一大步。获得50经费。",
     "name_en": "Reward!",
     "desc_en": "Your hard work has been recognized! Every small step is a giant leap toward success. Gain 50 funds.",
     "action": "fund", "amount": 50},
    {"id":  9, "name": "吃饭时间不要说话", "desc": "在太空吃饭边说话会使食物碎末飞出，容易呛到肺部发生危险。损失10经费。",
     "name_en": "No Talking While Eating",
     "desc_en": "Talking while eating in space lets food crumbs float into your lungs — dangerous! Lose 10 funds.",
     "action": "fund", "amount": -10},
    {"id": 10, "name": "虚心学习",         "desc": "向前方经验丰富的玩家学习，你的虚心学习让你所收获。获得30经费。",
     "name_en": "Learn Humbly",
     "desc_en": "Learning from experienced explorers ahead of you brings great rewards. Gain 30 funds.",
     "action": "fund", "amount": 30},
    {"id": 11, "name": "迷糊觉",           "desc": '太空舱内没有白天黑夜，宇航员的睡眠确实很"迷糊"。停止一轮。',
     "name_en": "Space Nap",
     "desc_en": 'No day or night in the capsule — astronaut sleep is truly "confusing". Skip a turn.',
     "action": "skip_turn"},
    {"id": 12, "name": "合格的探索者",     "desc": "每位探索者在行动之前都要经过漫长、艰苦的训练。损失50经费。",
     "name_en": "Rigorous Training",
     "desc_en": "Every explorer must undergo long, grueling training before setting out. Lose 50 funds.",
     "action": "fund", "amount": -50},
    {"id": 13, "name": "分享趣事",         "desc": "太空旅行中大多时间无聊乏味，偶尔大家分享趣事打发时间。本轮无事发生。",
     "name_en": "Share Fun Stories",
     "desc_en": "Space travel is mostly dull — sharing funny stories helps pass the time. Nothing happens this turn.",
     "action": "none"},
    {"id": 14, "name": "前往太空实验室",   "desc": "拍摄图片、影像和收集物质都是探索宇宙的重要方式。",
     "name_en": "Visit Space Lab",
     "desc_en": "Photos, videos, and sample collection are all important ways to explore the universe.",
     "action": "lab"},
]

# ─────────────────────────────
# 玩家上限
# ─────────────────────────────
MAX_PLAYERS = 6

# ─────────────────────────────
# 颜色配置（pygame RGB）
# ─────────────────────────────
COLORS = {
    "bg":          (15,  20,  40),   # 深蓝背景
    "board_bg":    (10,  15,  35),   # 棋盘背景
    "cell_planet": (30,  60, 120),   # 星球格
    "cell_start":  (200, 160,  0),   # 地球（出发点）
    "cell_event":  (140,  20,  20),  # 事件卡
    "cell_chance": (20,  100,  20),  # 机会卡
    "cell_safe":   (0,   120, 120),  # 宜居带
    "cell_jail":   (80,   80,  80),  # 空间站
    "cell_lab":    (100,   0, 150),  # 太空实验室
    "cell_bonus":  (0,   140,  70),  # 补给站(+)
    "cell_penalty":(140,  50,   0),  # 惩罚格
    "cell_border": (60,  100, 180),  # 格子边框
    "text_light":  (220, 230, 255),  # 浅色文字
    "text_dark":   (20,   20,  50),  # 深色文字
    "text_gold":   (255, 215,   0),  # 金色文字
    "panel_bg":    (20,  25,  55),   # 信息面板背景
    "button":      (40,  80, 160),   # 按钮
    "button_hover":(60, 110, 210),   # 按钮悬停
    "button_text": (255, 255, 255),  # 按钮文字
    "owned_p":     [                 # 玩家颜色（最多6人）
        (220,  60,  60),   # 玩家1 红
        (60,  180,  60),   # 玩家2 绿
        (60,  120, 220),   # 玩家3 蓝
        (220, 160,   0),   # 玩家4 黄
        (180,  60, 220),   # 玩家5 紫
        (40,  210, 200),   # 玩家6 青
    ],
    "dice_bg":     (40,  50,  90),
    "dice_dot":    (255, 255, 255),
}

# 每位玩家初始经费
STARTING_FUNDS = 200

# 经过地球奖励
PASS_EARTH_BONUS = 20
