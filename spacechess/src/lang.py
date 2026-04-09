# lang.py - Multi-language support / 多语言支持

_lang = "en"  # "zh" | "en"


def set_lang(lang: str):
    global _lang
    _lang = lang if lang in ("zh", "en") else "zh"


def get_lang() -> str:
    return _lang


def is_en() -> bool:
    return _lang == "en"


# ─────────────────────────────
# 字符串表 / String table
# ─────────────────────────────
_S = {
    # Player names
    "p0": {"zh": "玩家一", "en": "Player 1"},
    "p1": {"zh": "玩家二", "en": "Player 2"},
    "p2": {"zh": "玩家三", "en": "Player 3"},
    "p3": {"zh": "玩家四", "en": "Player 4"},
    "p4": {"zh": "玩家五", "en": "Player 5"},
    "p5": {"zh": "玩家六", "en": "Player 6"},

    # Start screen
    "title":          {"zh": "⭐  星际征途探索强手棋  ⭐",
                       "en": "⭐  Space Chess: Cosmic Explorer  ⭐"},
    "select_players": {"zh": "点击玩家图标选择参与人数",
                       "en": "Click a player icon to select number of players"},
    "n_players":      {"zh": "已选  {n}  人参与游戏", "en": "{n}  players selected"},
    "start_game":     {"zh": "开  始  游  戏",       "en": "Start  Game"},
    "credits":        {"zh": "基于《星际征途探索》桌游  |  Scratch 原版作者：hufuzhipeng",
                       "en": "Based on Space Explorer Board Game  |  Scratch original: hufuzhipeng"},

    # Panel
    "panel_title":    {"zh": "星际征途探索强手棋", "en": "Space Chess"},
    "turn":           {"zh": "当前: {name}",       "en": "Turn: {name}"},
    "players_status": {"zh": "── 玩家状态 ──",     "en": "── Players ──"},
    "player_planets": {"zh": "── {name}的星球 ──", "en": "── {name}'s Planets ──"},
    "no_planets":     {"zh": "（暂无星球）",        "en": "(No planets yet)"},
    "can_exp_tag":    {"zh": "[可实验]",            "en": "[Lab]"},
    "field_toll":     {"zh": "路费:",               "en": "Toll:"},
    "field_upgrade":  {"zh": "  升级:",             "en": "  Up:"},
    "field_trade":    {"zh": "  交易:",             "en": "  Trade:"},
    "field_mortgage": {"zh": "  抵押:",             "en": "  Mtg:"},
    "max_level":      {"zh": "满级",                "en": "Max"},

    # Buttons
    "btn_roll":        {"zh": "🎲  掷骰子",              "en": "🎲  Roll Dice"},
    "btn_buy":         {"zh": "✅  购买星球",             "en": "✅  Explore Planet"},
    "btn_skip":        {"zh": "❌  跳过",                "en": "❌  Skip"},
    "btn_pay":         {"zh": "💸  支付过路费",            "en": "💸  Pay Toll"},
    "btn_use_card":    {"zh": "🛡  使用免费卡（剩{n}张）", "en": "🛡  Use Free Pass ({n} left)"},
    "btn_upgrade":     {"zh": "⬆️  升级星球",             "en": "⬆️  Upgrade Planet"},
    "btn_trade":       {"zh": "🤝  收购星球（{cost}万）",  "en": "🤝  Trade Planet ({cost})"},
    "btn_skip_trade":  {"zh": "❌  跳过",                "en": "❌  Skip"},
    "btn_lab":         {"zh": "🔬  选择星球做实验",        "en": "🔬  Do Experiment"},
    "btn_skip_lab":    {"zh": "⏭️  跳过实验",            "en": "⏭️  Skip Lab"},
    "btn_earth_up":    {"zh": "⭐  免费升级星球",          "en": "⭐  Free Upgrade"},
    "btn_skip_earth":  {"zh": "❌  跳过",                "en": "❌  Skip"},
    "btn_mortgage":    {"zh": "🏦  选择星球交公",          "en": "🏦  Mortgage Planet"},
    "btn_next":        {"zh": "▶  继续游戏",             "en": "▶  Continue"},
    "btn_card_ok":     {"zh": "✅  确认",                "en": "✅  OK"},
    "btn_ch_roll":     {"zh": "🎲  再投骰子",            "en": "🎲  Roll Again"},
    "btn_ch_draw":     {"zh": "🃏  抽机会卡",            "en": "🃏  Draw Chance"},
    "btn_repo_n":      {"zh": "✅  确认调配（剩余 {n} 次）", "en": "✅  Confirm ({n} moves left)"},
    "btn_repo_0":      {"zh": "✅  完成调配",             "en": "✅  Done"},

    # Picker popups
    "picker_mortgage": {"zh": "选择一颗星球交公（换钱还债）",       "en": "Select a planet to mortgage"},
    "picker_lab":      {"zh": "选择一颗星球做实验（免费升级）",      "en": "Select a planet for experiment"},
    "picker_earth":    {"zh": "选择一颗星球免费升级",               "en": "Select a planet for free upgrade"},
    "picker_explore":  {"zh": "选择一颗未被探索的星球（免费探索）",   "en": "Select an unexplored planet (free)"},
    "picker_exp_type": {"zh": "选择实验类型 — {name}",             "en": "Choose Experiment — {name}"},
    "picker_no_planet":{"zh": "没有星球可操作",                    "en": "No planets available"},
    "picker_lab_done": {"zh": " (实验已全部完成)",                  "en": " (All done)"},
    "picker_cost":     {"zh": "  探索费:{n}",                      "en": "  Cost:{n}"},

    # Planet card popup
    "col_lv":          {"zh": "探索等级", "en": "Level"},
    "col_exp_fee":     {"zh": "探索费",   "en": "Explore"},
    "col_toll":        {"zh": "过路费",   "en": "Toll"},
    "col_trade":       {"zh": "收购费",   "en": "Trade"},
    "col_mtg":         {"zh": "交公价",   "en": "Mortgage"},
    "exp_label":       {"zh": "实验项目：", "en": "Experiments: "},
    "exp_formula_p":   {"zh": "（做一次实验可免费升一级，提高过路费）",
                        "en": "(Each experiment = free upgrade + higher toll)"},
    "no_exp":          {"zh": "无",       "en": "None"},
    "fun_facts":       {"zh": "趣味知识", "en": "Fun Facts"},
    "planet_owner":    {"zh": "持有者：{name}　　当前等级：{lv}",
                        "en": "Owner: {name}     Level: {lv}"},
    "planet_no_owner": {"zh": "此星球尚未被探索", "en": "Unexplored"},

    # Level names (0-3)
    "lv0": {"zh": "观测",       "en": "Observation"},
    "lv1": {"zh": "卫星探测",   "en": "Satellite Probe"},
    "lv2": {"zh": "着陆车探测", "en": "Rover Probe"},
    "lv3": {"zh": "成功探索",   "en": "Full Exploration"},

    # Card types
    "card_event":  {"zh": "事件卡", "en": "Event Card"},
    "card_chance": {"zh": "机会卡", "en": "Chance Card"},

    # Experiment names (0-2)
    "exp0":         {"zh": "采集矿物", "en": "Mining"},
    "exp1":         {"zh": "水实验",   "en": "Water Test"},
    "exp2":         {"zh": "植物实验", "en": "Plant Test"},
    "exp_done_lbl": {"zh": "✓  {name}  (已完成)", "en": "✓  {name}  (Done)"},
    "exp_formula":  {"zh": "（每次实验免费升一级，提高过路费）",
                     "en": "(Each experiment = free upgrade)"},

    # Fund notice
    "fund_title":   {"zh": "💰  资金变动",  "en": "💰  Fund Changes"},
    "fund_ok":      {"zh": "✅  确认",      "en": "✅  OK"},
    "fund_amount":  {"zh": "{b}万 → {a}万  （{s}{d}万）", "en": "{b} → {a}  ({s}{d})"},

    # Skip notice
    "skip_notice_title": {"zh": "本轮跳过", "en": "Skip Turn"},
    "skip_notice_ok":    {"zh": "知道了",   "en": "Got it"},

    # Reposition overlay
    "repo_title": {"zh": "调配探索者 ─ {name} 操作中    剩余次数：{n}/3",
                   "en": "Reposition ─ {name}'s turn     Moves left: {n}/3"},

    # Game over
    "over_title":  {"zh": "🏆  游戏结束  🏆", "en": "🏆  Game Over  🏆"},
    "over_winner": {"zh": "{name} 获胜！",     "en": "{name} wins!"},
    "over_rank":   {"zh": "第 {i} 名  {name}  总资产: {w}",
                    "en": "#{i}  {name}    Net worth: {w}"},
    "play_again":  {"zh": "再来一局",          "en": "Play Again"},

    # Music
    "music_on":    {"zh": "🔊 M", "en": "🔊 M"},
    "music_off":   {"zh": "🔇 M", "en": "🔇 M"},

    # ── Fund notice reasons (shown in fund change popup) ──
    "r_pass_earth":  {"zh": "经过地球×{n}",         "en": "Pass Earth ×{n}"},
    "r_land_earth":  {"zh": "精确踏上地球",          "en": "Land on Earth"},
    "r_explore":     {"zh": "探索{name}",            "en": "Explore {name}"},
    "r_upgrade":     {"zh": "升级{name}→Lv{lv}",    "en": "Upgrade {name} →Lv{lv}"},
    "r_toll_pay":    {"zh": "过路费",                "en": "Toll"},
    "r_toll_recv":   {"zh": "收取过路费",            "en": "Collect Toll"},
    "r_mortgage":    {"zh": "交公{name}",            "en": "Mortgage {name}"},
    "r_trade_buy":   {"zh": "收购{name}",            "en": "Trade {name}"},
    "r_trade_sell":  {"zh": "出售{name}",            "en": "Sell {name}"},
    "r_card":        {"zh": "卡牌：{name}",          "en": "Card: {name}"},
    "r_cell":        {"zh": "{name}",                "en": "{name}"},
    "r_pass_move":   {"zh": "经过地球",              "en": "Pass Earth"},
    "r_share":       {"zh": "分享财富",              "en": "Share Funds"},

    # ── Game messages (gs.message) ──
    "msg_start":           {"zh": "{name}，请掷骰子！",
                            "en": "{name}, roll the dice!"},
    "msg_triple":          {"zh": "{name} 三连双数！被送入空间站。",
                            "en": "{name} rolled triple doubles! Sent to Space Station."},
    "msg_pass_earth":      {"zh": "{name} 经过地球，获得 {bonus} 经费！",
                            "en": "{name} passed Earth! Gained {bonus} funds."},
    "msg_land_earth":      {"zh": "{name} 精确踏上地球！获得 {bonus} 经费。",
                            "en": "{name} landed on Earth! Gained {bonus} funds."},
    "msg_land_earth_up":   {"zh": "\n可免费升级一颗星球！",
                            "en": "\nFree planet upgrade available!"},
    "msg_penalty":         {"zh": "{name} 落在【{cell}】，损失 {amt} 经费！",
                            "en": "{name} landed on {cell}! Lost {amt} funds."},
    "msg_penalty_broke":   {"zh": "\n经费不足，请选择星球交公！",
                            "en": "\nInsufficient funds! Mortgage a planet."},
    "msg_bonus_gain":      {"zh": "{name} 落在【{cell}】，获得 {amt} 经费！",
                            "en": "{name} landed on {cell}! Gained {amt} funds."},
    "msg_bonus_pay":       {"zh": "{name} 落在【{cell}】，支付 {amt} 经费。",
                            "en": "{name} landed on {cell}. Paid {amt} funds."},
    "msg_jail_enter":      {"zh": "{name} 进入空间站，停走一轮！",
                            "en": "{name} entered the Space Station! Skip next turn."},
    "msg_safe_zone":       {"zh": "{name} 到达宜居带！加速探索，可再投一次骰子！",
                            "en": "{name} reached the Habitable Zone! Roll again!"},
    "msg_lab_land":        {"zh": "{name} 到达太空实验室，可以对自己的星球做实验！",
                            "en": "{name} reached the Space Lab! Conduct an experiment."},
    "msg_planet_buy_q":    {"zh": "【{planet}】\n探索费用: {cost} 经费\n过路费(Lv1): {toll} 经费\n{name} 是否购买？",
                            "en": "{planet}\nExplore cost: {cost}\nToll (Lv1): {toll}\n{name}: explore?"},
    "msg_planet_up_q":     {"zh": "【{planet}】当前 Lv{lv}\n升级费用: {cost} 经费\n升级后过路费: {toll} 经费\n是否升级到 Lv{nlv}？",
                            "en": "{planet}  Lv{lv}\nUpgrade cost: {cost}\nNew toll: {toll}\nUpgrade to Lv{nlv}?"},
    "msg_planet_max":      {"zh": "【{planet}】Lv{lv} 已是最高级\n当前过路费: {toll} 经费",
                            "en": "{planet}  Lv{lv} (Max)\nCurrent toll: {toll}"},
    "msg_planet_pay_card": {"zh": "【{planet}】属于 {owner}\n{lv_line}\n过路费：{toll} 经费\n你有免费卡，是否使用？",
                            "en": "{planet} — owned by {owner}\n{lv_line}\nToll: {toll}\nUse free pass?"},
    "msg_planet_pay":      {"zh": "【{planet}】属于 {owner}\n{lv_line}\n过路费：{toll} 经费",
                            "en": "{planet} — owned by {owner}\n{lv_line}\nToll: {toll}"},
    "msg_lv_line":         {"zh": "等级：Lv{lv}·{lv_name}{exp_note}",
                            "en": "Level: Lv{lv}·{lv_name}{exp_note}"},
    "msg_exp_note":        {"zh": "，含{n}次实验升级",
                            "en": " (+{n} exp. upgrades)"},
    "msg_buy_ok":          {"zh": "{name} 探索了【{planet}】！花费 {cost} 经费。",
                            "en": "{name} explored {planet}! Cost: {cost} funds."},
    "msg_buy_fail":        {"zh": "{name} 经费不足，无法购买！",
                            "en": "{name} has insufficient funds!"},
    "msg_up_ok":           {"zh": "{name} 将【{planet}】升级到 Lv{lv}！花费 {cost} 经费。",
                            "en": "{name} upgraded {planet} to Lv{lv}! Cost: {cost}."},
    "msg_up_fail":         {"zh": "{name} 经费不足，无法升级！",
                            "en": "{name} has insufficient funds to upgrade!"},
    "msg_up_max":          {"zh": "【{planet}】已是最高级，无法升级！",
                            "en": "{planet} is already max level!"},
    "msg_use_card":        {"zh": "{name} 使用了免费卡，免付过路费！",
                            "en": "{name} used a free pass! No toll paid."},
    "msg_pay_toll":        {"zh": "{name} 支付 {toll} 经费给 {owner}。",
                            "en": "{name} paid {toll} funds to {owner}."},
    "msg_pay_trade_q":     {"zh": "\n是否花 {cost} 经费收购【{planet}】Lv{lv}？",
                            "en": "\nSpend {cost} to acquire {planet} Lv{lv}?"},
    "msg_pay_fail":        {"zh": "{name} 经费不足（需 {toll}，有 {funds}）！\n请选择一颗星球交公换钱。",
                            "en": "{name} can't pay toll (need {toll}, have {funds})!\nMortgage a planet."},
    "msg_mortgage_ok":     {"zh": "{name} 将【{planet}】交公，获得 {cash} 经费。",
                            "en": "{name} mortgaged {planet} for {cash} funds."},
    "msg_bankrupt":        {"zh": "💥 {name} 破产出局！",
                            "en": "💥 {name} is bankrupt!"},
    "msg_game_over":       {"zh": "🏆 游戏结束！{name} 获胜！",
                            "en": "🏆 Game Over! {name} wins!"},
    "msg_card_event":      {"zh": "{name} 抽到事件卡：【{card}】\n{desc}",
                            "en": "{name} drew Event Card: {card}\n{desc}"},
    "msg_card_chance":     {"zh": "{name} 抽到机会卡：【{card}】\n{desc}",
                            "en": "{name} drew Chance Card: {card}\n{desc}"},
    "msg_teleport_to":     {"zh": "\n传送到{cell}！",
                            "en": "\nTeleported to {cell}!"},
    "msg_reverse":         {"zh": "\n下一轮将反向移动！",
                            "en": "\nNext turn: move in reverse!"},
    "msg_moved":           {"zh": "\n移动了 {steps} 格。",
                            "en": "\nMoved {steps} spaces."},
    "msg_jail_card":       {"zh": "\n进入空间站，停走一轮！",
                            "en": "\nSent to Space Station! Skip next turn."},
    "msg_extra_roll":      {"zh": "\n本轮可以再投一次骰子！",
                            "en": "\nBonus roll this turn!"},
    "msg_keep_full":       {"zh": "\n已持有免过路费卡，此卡返还。（最多持有1张）",
                            "en": "\nAlready have a free pass. Card returned. (Max 1)"},
    "msg_keep_ok":         {"zh": "\n已保存免过路费卡！",
                            "en": "\nFree pass saved!"},
    "msg_lab_teleport":    {"zh": "{name} 传送到太空实验室！",
                            "en": "{name} teleported to Space Lab!"},
    "msg_skip_next":       {"zh": "\n下一轮停走！",
                            "en": "\nSkip next turn!"},
    "msg_reset":           {"zh": "\n返回地球，经费重置为 {funds}！",
                            "en": "\nReturn to Earth! Funds reset to {funds}."},
    "msg_comet_jail":      {"zh": "\n拥有彗星的玩家停走一轮：{names}",
                            "en": "\nComet planet owners skip a turn: {names}"},
    "msg_comet_none":      {"zh": "\n当前无人拥有彗星星球，无效果。",
                            "en": "\nNo comet planet owners. No effect."},
    "msg_give_fund_q":     {"zh": "选择要给予 {amt} 经费的玩家",
                            "en": "Choose a player to give {amt} funds to"},
    "msg_no_others":       {"zh": "\n无其他玩家，无效果。",
                            "en": "\nNo other players. No effect."},
    "msg_swap_no_planet":  {"zh": "\n没有可互换的星球。",
                            "en": "\nNo planets available to swap."},
    "msg_swap_q":          {"zh": "选择要互换星球的玩家",
                            "en": "Choose a player to swap planets with"},
    "msg_explore_free":    {"zh": "选择一颗未被探索的星球免费探索！",
                            "en": "Choose an unclaimed planet to explore for free!"},
    "msg_explore_none":    {"zh": "\n所有星球已被探索，无效果。",
                            "en": "\nAll planets explored. No effect."},
    "msg_chance_roll":     {"zh": "{name} 选择再投一次骰子！",
                            "en": "{name} chose to roll again!"},
    "msg_chance_draw":     {"zh": "{name} 选择抽一张机会卡！",
                            "en": "{name} chose to draw a Chance Card!"},
    "msg_fund_delta":      {"zh": "\n资金变化：{s}{amt}",
                            "en": "\nFunds: {s}{amt}"},
    "msg_all_fund":        {"zh": "\n所有玩家资金变化：{s}{amt}",
                            "en": "\nAll players funds: {s}{amt}"},
    "msg_give_ok":         {"zh": "{name} 给了 {target} {amt} 经费！",
                            "en": "{name} gave {amt} funds to {target}!"},
    "msg_give_fail":       {"zh": "{name} 经费不足，无法分享。",
                            "en": "{name} has insufficient funds to share."},
    "msg_swap_mine":       {"zh": "选择你要给出的星球（换给 {target}）",
                            "en": "Choose your planet to give to {target}"},
    "msg_swap_theirs":     {"zh": "选择从 {target} 获得的星球",
                            "en": "Choose a planet to receive from {target}"},
    "msg_swap_cancel":     {"zh": "星球状态已改变，取消互换。",
                            "en": "Planet status changed. Swap cancelled."},
    "msg_swap_ok":         {"zh": "{name} 和 {target} 互换了 {p1} ↔ {p2}！",
                            "en": "{name} and {target} swapped {p1} ↔ {p2}!"},
    "msg_explore_free_ok": {"zh": "{name} 免费探索了【{planet}】！",
                            "en": "{name} explored {planet} for free!"},
    "msg_explore_free_no": {"zh": "星球已被占领，无效。",
                            "en": "Planet already claimed."},
    "msg_exp_done":        {"zh": "【{planet}】的{exp}已完成，不能重复做。",
                            "en": "{planet}'s {exp} is already done."},
    "msg_exp_no":          {"zh": "【{planet}】不支持实验。",
                            "en": "{planet} doesn't support experiments."},
    "msg_exp_max":         {"zh": "【{planet}】已达最高级，无法再做实验。",
                            "en": "{planet} is at max level."},
    "msg_exp_ok":          {"zh": "{name} 在【{planet}】完成{exp}！\n免费升至 Lv{lv}，通行费 {old} → {new}。",
                            "en": "{name} completed {exp} on {planet}!\nFree upgrade to Lv{lv}, toll: {old} → {new}."},
    "msg_reposition":      {"zh": "{name} 调配探索者！\n拖动其他玩家的棋子到目标格子（共3次机会）",
                            "en": "{name} repositions explorers!\nDrag other players' tokens (3 moves)."},
    "msg_reposition_move": {"zh": "{player} → {cell}（剩余 {n} 次）",
                            "en": "{player} → {cell} ({n} moves left)"},
    "msg_trade_ok":        {"zh": "{name} 花 {cost} 经费收购了【{planet}】！",
                            "en": "{name} acquired {planet} for {cost} funds!"},
    "msg_trade_fail":      {"zh": "{name} 经费不足，无法收购！",
                            "en": "{name} has insufficient funds to acquire!"},
    "msg_broke_mortgage":  {"zh": "\n经费不足，请选择星球交公！",
                            "en": "\nInsufficient funds! Mortgage a planet."},

    # ── Additional game messages ──
    "msg_extra_roll_turn": {"zh": "\n（双数！可以再投一次！）",
                            "en": "\n(Doubles! Roll again!)"},
    "msg_turn_start":      {"zh": "轮到 {name} 了，请掷骰子！",
                            "en": "{name}'s turn — roll the dice!"},
    "msg_skip_notice":     {"zh": "由于「{reason}」，{name} 本轮跳过。",
                            "en": "{name} skips this turn ({reason})."},
    "msg_earth_up_max":    {"zh": "【{planet}】已是最高级。",
                            "en": "{planet} is already max level."},
    "msg_earth_up_ok":     {"zh": "{name} 免费将【{planet}】升级到 Lv{lv}！通行费提升至 {toll}。",
                            "en": "{name} free-upgraded {planet} to Lv{lv}! Toll is now {toll}."},
    # Jailed reasons (shown in skip notice)
    "reason_triple":       {"zh": "三连双数",   "en": "Triple Doubles"},
    "reason_jail":         {"zh": "进入空间站", "en": "Space Station"},
    "reason_comet":        {"zh": "彗星干扰",   "en": "Comet Disruption"},
    "reason_skip":         {"zh": "停走一轮",   "en": "Skip Turn"},

    # List separator
    "sep_comma":           {"zh": "、", "en": ", "},
}


def t(key: str, **kwargs) -> str:
    """Return the string for the current language, with optional format args."""
    entry = _S.get(key)
    if entry is None:
        return key
    s = entry.get(_lang) or entry.get("zh") or key
    if kwargs:
        try:
            return s.format(**kwargs)
        except (KeyError, IndexError):
            return s
    return s


def lv_name(i: int) -> str:
    """Return level name for index 0-3."""
    return t(f"lv{i}")


def exp_name(i: int) -> str:
    """Return experiment name for index 0-2."""
    return t(f"exp{i}")


def player_name(i: int) -> str:
    """Return player name for index 0-3."""
    return t(f"p{i}")


def loc_name(d: dict) -> str:
    """Return the localised name from a dict that has 'name' and optionally 'name_en'."""
    if is_en():
        return d.get("name_en") or d["name"]
    return d["name"]
