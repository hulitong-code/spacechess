# game.py - 星际征途探索强手棋 游戏逻辑

import random
import copy
import lang as _lang
from data import (BOARD, PLANETS, CELL_PLANET_ID,
                  EVENT_CARDS, CHANCE_CARDS,
                  STARTING_FUNDS, PASS_EARTH_BONUS, COMET_PLANET_IDS,
                  MAX_PLAYERS)


def _pname(pdata):
    """Planet name in current language."""
    if _lang.is_en():
        return pdata.get("name_en") or pdata["name"]
    return pdata["name"]


def _cname(cell):
    """Board cell name in current language."""
    if _lang.is_en():
        return cell.get("name_en") or cell["name"]
    return cell["name"]

# ─────────────────────────────
# 玩家
# ─────────────────────────────
class Player:
    EMOJIS = ["🔴", "🟢", "🔵", "🟡", "🟣", "🩵"]

    def __init__(self, player_id: int):
        self.id       = player_id          # 0-indexed
        self.name     = _lang.player_name(player_id)
        self.pos      = 0                  # 当前格子索引 (0=地球)
        self.funds    = STARTING_FUNDS
        self.planets  = {}                 # {planet_id: level(0-3)}
        self.planet_exps = {}              # {planet_id: [done_mining, done_water, done_plant]}
        self.jailed   = 0                  # >0 = 在空间站还剩几轮
        self.jailed_reason = ""             # 停走原因（用于提示）
        self.reverse  = False              # 下一轮是否反向移动
        self.keep_cards = 0                # 持有的"免过路费"卡数量
        self.bankrupt = False

    def move(self, steps: int):
        """移动 steps 格，返回经过地球的次数（用于奖励）"""
        direction = -1 if self.reverse else 1
        self.reverse = False
        total = len(BOARD)
        old   = self.pos
        new   = (old + direction * steps) % total
        # 计算经过地球次数
        if direction > 0:
            passed = 1 if new < old else 0   # 绕过0点（正向）
            if steps == 0:
                passed = 0
        else:
            passed = 1 if (steps > 0 and new > old) else 0  # 反向绕过0点
        self.pos = new
        return passed

    def teleport(self, cell: int):
        """直接传送到指定格，不计算过地球"""
        self.pos = cell % len(BOARD)

    def pay(self, amount: int) -> bool:
        """支付金额，返回是否成功"""
        if self.funds >= amount:
            self.funds -= amount
            return True
        return False

    def earn(self, amount: int):
        self.funds += amount

    @property
    def net_worth(self):
        """总资产 = 现金 + 所有星球交公价值"""
        total = self.funds
        for pid, lv in self.planets.items():
            total += PLANETS[pid]["levels"][lv]["mortgage"]
        return total

    def __repr__(self):
        return f"{self.name}(pos={self.pos}, funds={self.funds})"


# ─────────────────────────────
# 游戏状态
# ─────────────────────────────
class GamePhase:
    ROLL          = "roll"
    MOVING        = "moving"
    PLANET_BUY    = "planet_buy"
    PLANET_PAY    = "planet_pay"
    PLANET_UP     = "planet_up"
    PLANET_TRADE  = "planet_trade"
    EARTH_UPGRADE = "earth_upgrade"
    LAB           = "lab"
    CARD          = "card"
    REPOSITION    = "reposition"
    EXPLORE_FREE  = "explore_free"
    FUND_NOTICE   = "fund_notice"   # 资金变动通知
    SKIP_NOTICE   = "skip_notice"   # 停走通知
    GIVE_FUND     = "give_fund"     # 选择给经费的目标玩家
    SWAP_PLAYER   = "swap_player"   # 互换星球·第1步：选目标玩家
    SWAP_MINE     = "swap_mine"     # 互换星球·第2步：选自己给出的星球
    SWAP_THEIRS   = "swap_theirs"   # 互换星球·第3步：选对方给出的星球
    MORTGAGE      = "mortgage"
    BANKRUPT      = "bankrupt"
    GAME_OVER     = "game_over"


class GameState:
    def __init__(self, num_players: int):
        assert 2 <= num_players <= MAX_PLAYERS
        self.players      = [Player(i) for i in range(num_players)]
        self.current_idx  = 0
        self.dice         = (0, 0)
        self.double_count = 0
        self.extra_roll       = False
        self._reposition_moves = 0
        self.phase        = GamePhase.ROLL
        self.message      = ""
        self.pending_toll = 0
        self.pending_to   = -1
        self.pending_pid  = -1
        self.current_card = None
        self.fund_events  = []              # [{name, before, after, reason}]
        self._resume_phase = GamePhase.ROLL # FUND_NOTICE 后恢复的阶段
        self._setup_card_decks()
        # 记录最后移动步数（用于"反向移动相同步数"）
        self._last_steps  = 0
        # 分享财富 / 互换星球 中间状态
        self._give_fund_amt  = 0
        self._swap_target_id = -1
        self._swap_my_pid    = -1

    def _setup_card_decks(self):
        self.event_deck  = list(EVENT_CARDS)
        self.chance_deck = list(CHANCE_CARDS)
        random.shuffle(self.event_deck)
        random.shuffle(self.chance_deck)

    def _record_fund(self, player: Player, delta: int, reason: str):
        """记录一次资金变化（在变化后调用，delta>0=收入，delta<0=支出）"""
        self.fund_events.append({
            "name":   player.name,
            "before": player.funds - delta,
            "after":  player.funds,
            "reason": reason,
        })

    def _maybe_show_fund_notice(self):
        """如有未显示的资金变化，切换到通知阶段；否则不动"""
        if self.fund_events and self.phase != GamePhase.FUND_NOTICE:
            self._resume_phase = self.phase
            self.phase = GamePhase.FUND_NOTICE

    def confirm_fund_notice(self):
        """玩家点击确认后，清除记录并恢复原阶段"""
        self.fund_events.clear()
        self.phase = self._resume_phase

    @property
    def current_player(self) -> Player:
        return self.players[self.current_idx]

    @property
    def active_players(self):
        return [p for p in self.players if not p.bankrupt]

    # ── 掷骰子 ──────────────────
    def roll_dice(self):
        """掷两个骰子，返回 (d1, d2)"""
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.dice = (d1, d2)
        return d1, d2

    def process_roll(self):
        """
        处理掷骰子后的移动逻辑。
        返回事件字符串，UI 据此更新。
        """
        d1, d2 = self.dice
        steps  = d1 + d2
        is_double = (d1 == d2)
        player = self.current_player

        if is_double:
            self.double_count += 1
        else:
            self.double_count = 0

        # 三连双数 → 进空间站
        if self.double_count >= 3:
            self.double_count = 0
            player.jailed = 1
            player.jailed_reason = "triple"
            player.teleport(16)   # 空间站 = 格17, 索引16
            self.phase   = GamePhase.ROLL
            self.message = _lang.t("msg_triple", name=player.name)
            return "jail"

        self._last_steps = steps
        passed_earth = player.move(steps)

        # 经过地球奖励
        for _ in range(passed_earth):
            player.earn(PASS_EARTH_BONUS)
            self.message = _lang.t("msg_pass_earth", name=player.name, bonus=PASS_EARTH_BONUS)

        # 再投一次（双数且未三连）
        if is_double and self.double_count < 3:
            self.extra_roll = True

        return self._handle_cell(player)

    # ── 动画分离接口 ─────────────────
    def begin_roll(self):
        """骰子动画结束后调用：处理双数/空间站检测。
        返回 (steps, direction, instant)：
          steps     = 动画移动格数（0 表示不移动）
          direction = +1 正向 / -1 反向
          instant   = None 或 'jail'（三连双数直接进空间站）
        调用方执行逐格动画后，再调用 finish_roll()。"""
        d1, d2    = self.dice
        steps     = d1 + d2
        is_double = (d1 == d2)
        player    = self.current_player

        if is_double:
            self.double_count += 1
        else:
            self.double_count = 0

        if self.double_count >= 3:
            self.double_count = 0
            player.jailed = 1
            player.jailed_reason = "triple"
            player.teleport(16)
            self.message = _lang.t("msg_triple", name=player.name)
            self.phase   = GamePhase.MOVING
            return 0, 1, "jail"

        self._last_steps = steps
        if is_double:
            self.extra_roll = True
        direction      = -1 if player.reverse else 1
        player.reverse = False
        self.phase     = GamePhase.MOVING
        return steps, direction, None

    def finish_roll(self, passed_earth: int = 0):
        """逐格动画完毕后调用：奖励过地球经费，处理落点事件。"""
        player = self.current_player
        if passed_earth > 0:
            bonus = PASS_EARTH_BONUS * passed_earth
            player.earn(bonus)
            self._record_fund(player, bonus, _lang.t("r_pass_earth", n=passed_earth))
            self.message = _lang.t("msg_pass_earth", name=player.name, bonus=bonus)
        result = self._handle_cell(player)
        self._maybe_show_fund_notice()
        return result

    def end_jail_turn(self):
        """三连双数进空间站后直接结束回合。"""
        self._next_player()

    def _handle_cell(self, player: Player) -> str:
        """处理玩家落点事件，返回事件类型字符串"""
        cell = BOARD[player.pos]
        ctype = cell["type"]

        if ctype == "start":
            player.earn(PASS_EARTH_BONUS)
            self._record_fund(player, PASS_EARTH_BONUS, _lang.t("r_land_earth"))
            self.message = _lang.t("msg_land_earth", name=player.name, bonus=PASS_EARTH_BONUS)
            upgradeable = [pid for pid, lv in player.planets.items()
                           if self._next_upgrade_level(pid, lv) is not None]
            if upgradeable:
                self.phase = GamePhase.EARTH_UPGRADE
                self.message += _lang.t("msg_land_earth_up")
            else:
                self._end_turn_or_extra()
            return "start"

        elif ctype == "planet":
            return self._handle_planet(player, cell)

        elif ctype == "event":
            return self._draw_event(player)

        elif ctype == "chance":
            return self._draw_chance(player)

        elif ctype == "penalty":
            amt = abs(cell["amount"])
            player.funds -= amt          # 强制扣除（可能变负）
            self._record_fund(player, -amt, _lang.t("r_cell", name=_cname(cell)))
            self.message = _lang.t("msg_penalty", name=player.name, cell=_cname(cell), amt=amt)
            if player.funds < 0:
                if player.planets:
                    self.phase   = GamePhase.MORTGAGE
                    self.message += _lang.t("msg_penalty_broke")
                else:
                    player.funds = 0
                    self._declare_bankrupt(player)
            else:
                self._end_turn_or_extra()
            return "penalty"

        elif ctype == "bonus":
            amt = cell["amount"]
            if amt > 0:
                player.earn(amt)
                self._record_fund(player, amt, _lang.t("r_cell", name=_cname(cell)))
                self.message = _lang.t("msg_bonus_gain", name=player.name, cell=_cname(cell), amt=amt)
            else:
                player.pay(abs(amt))
                self._record_fund(player, -abs(amt), _lang.t("r_cell", name=_cname(cell)))
                self.message = _lang.t("msg_bonus_pay", name=player.name, cell=_cname(cell), amt=abs(amt))
            self._end_turn_or_extra()
            return "bonus"

        elif ctype == "jail":
            player.jailed = 1
            player.jailed_reason = "jail"
            self.message = _lang.t("msg_jail_enter", name=player.name)
            self._end_turn_or_extra()
            return "jail"

        elif ctype == "safe":
            self.extra_roll = True
            self.phase   = GamePhase.ROLL
            self.message = _lang.t("msg_safe_zone", name=player.name)
            return "safe"

        elif ctype == "lab":
            self.phase   = GamePhase.LAB
            self.message = _lang.t("msg_lab_land", name=player.name)
            return "lab"

        self._end_turn_or_extra()
        return "none"

    # ── 星球处理 ────────────────
    def _handle_planet(self, player: Player, cell: dict) -> str:
        pid = cell["planet_id"]
        pdata = PLANETS[pid]

        # 找这颗星球的主人
        owner = self._find_planet_owner(pid)

        if owner is None:
            # 无主星球 → 询问是否购买
            cost = pdata["levels"][0]["explore"]
            toll0 = pdata["levels"][0]["toll"]
            self.message = _lang.t("msg_planet_buy_q",
                                   planet=_pname(pdata), cost=cost,
                                   toll=toll0, name=player.name)
            self.phase = GamePhase.PLANET_BUY
            return "planet_buy"

        elif owner.id == player.id:
            # 自己的星球 → 询问是否升级
            lv = player.planets[pid]
            next_lv = self._next_upgrade_level(pid, lv)
            if next_lv is not None:
                next_cost = pdata["levels"][next_lv]["explore"]
                next_toll = pdata["levels"][next_lv]["toll"]
                self.message = _lang.t("msg_planet_up_q",
                                       planet=_pname(pdata), lv=lv+1,
                                       cost=next_cost, toll=next_toll, nlv=next_lv+1)
                self.phase = GamePhase.PLANET_UP
                return "planet_up"
            cur_toll = pdata["levels"][lv]["toll"]
            self.message = _lang.t("msg_planet_max",
                                   planet=_pname(pdata), lv=lv+1, toll=cur_toll)
            self._end_turn_or_extra()
            return "own_max"

        else:
            # 别人的星球 → 支付过路费
            lv = owner.planets[pid]
            toll = pdata["levels"][lv]["toll"]
            self.pending_toll = toll
            self.pending_to   = owner.id
            self.pending_pid  = pid
            exp_count = sum(owner.planet_exps.get(pid, [False, False, False]))
            exp_note  = _lang.t("msg_exp_note", n=exp_count) if exp_count > 0 else ""
            lv_line   = _lang.t("msg_lv_line",
                                 lv=lv+1, lv_name=_lang.lv_name(lv), exp_note=exp_note)
            if player.keep_cards > 0:
                self.message = _lang.t("msg_planet_pay_card",
                                       planet=_pname(pdata), owner=owner.name,
                                       lv_line=lv_line, toll=toll)
                self.phase = GamePhase.PLANET_PAY
            else:
                self.message = _lang.t("msg_planet_pay",
                                       planet=_pname(pdata), owner=owner.name,
                                       lv_line=lv_line, toll=toll)
                self.phase = GamePhase.PLANET_PAY
            return "planet_pay"

    def _find_planet_owner(self, planet_id: int):
        for p in self.players:
            if not p.bankrupt and planet_id in p.planets:
                return p
        return None

    def _next_upgrade_level(self, pid: int, current_lv: int):
        """返回下一个有效升级等级（跳过 explore=0 且 toll=0 的空白等级）。无则返回 None。"""
        for lv in range(current_lv + 1, 4):
            lvdata = PLANETS[pid]["levels"][lv]
            if lvdata["explore"] > 0 or lvdata["toll"] > 0:
                return lv
        return None

    # ── 购买 / 升级 确认 ─────────
    def confirm_buy_planet(self):
        """玩家选择购买当前落点的星球"""
        player = self.current_player
        pid = CELL_PLANET_ID[player.pos]
        cost = PLANETS[pid]["levels"][0]["explore"]
        if player.pay(cost):
            player.planets[pid] = 0
            player.planet_exps[pid] = [False, False, False]
            self._record_fund(player, -cost, _lang.t("r_explore", name=_pname(PLANETS[pid])))
            self.message = _lang.t("msg_buy_ok", name=player.name,
                                   planet=_pname(PLANETS[pid]), cost=cost)
        else:
            self.message = _lang.t("msg_buy_fail", name=player.name)
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    def confirm_upgrade_planet(self):
        """玩家选择升级当前落点的星球"""
        player = self.current_player
        pid = CELL_PLANET_ID[player.pos]
        lv = player.planets[pid]
        next_lv = self._next_upgrade_level(pid, lv)
        if next_lv is None:
            self.message = _lang.t("msg_up_max", planet=_pname(PLANETS[pid]))
            self._end_turn_or_extra()
            return
        cost = PLANETS[pid]["levels"][next_lv]["explore"]
        if player.pay(cost):
            player.planets[pid] = next_lv
            self._record_fund(player, -cost,
                              _lang.t("r_upgrade", name=_pname(PLANETS[pid]), lv=next_lv+1))
            self.message = _lang.t("msg_up_ok", name=player.name,
                                   planet=_pname(PLANETS[pid]), lv=next_lv+1, cost=cost)
        else:
            self.message = _lang.t("msg_up_fail", name=player.name)
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    def confirm_pay_toll(self, use_keep_card=False):
        """玩家选择支付过路费"""
        player = self.current_player
        toll   = self.pending_toll
        owner  = self.players[self.pending_to]

        if use_keep_card and player.keep_cards > 0:
            player.keep_cards -= 1
            self.message = _lang.t("msg_use_card", name=player.name)
            self.pending_toll = 0
            self.pending_to   = -1
            self.pending_pid  = -1
            self._end_turn_or_extra()
            return

        if player.pay(toll):
            owner.earn(toll)
            self._record_fund(player, -toll, _lang.t("r_toll_pay"))
            self._record_fund(owner,  +toll, _lang.t("r_toll_recv"))
            self.message = _lang.t("msg_pay_toll", name=player.name, toll=toll, owner=owner.name)
            self.pending_toll = 0
            self.pending_to   = -1
            # 支付过路费后，询问是否收购
            pid = self.pending_pid
            if pid >= 0:
                pdata = PLANETS[pid]
                lv    = owner.planets[pid]
                trade_cost = pdata["levels"][lv]["trade"]
                next_lv = self._next_upgrade_level(pid, lv)
                if trade_cost > 0 and next_lv is not None:
                    self.phase = GamePhase.PLANET_TRADE
                    self.message += _lang.t("msg_pay_trade_q",
                                            cost=trade_cost, planet=_pname(pdata), lv=lv+1)
                    self._maybe_show_fund_notice()
                    return
            self.pending_pid = -1
            self._end_turn_or_extra()
            self._maybe_show_fund_notice()
        else:
            # 钱不够 → 进入交公流程
            self.phase   = GamePhase.MORTGAGE
            self.message = _lang.t("msg_pay_fail",
                                   name=player.name, toll=toll, funds=player.funds)

    # ── 交公（强制变卖星球）────────
    def mortgage_planet(self, planet_id: int):
        """将指定星球变卖回银行"""
        player = self.current_player
        if planet_id not in player.planets:
            return
        lv   = player.planets[planet_id]
        cash = PLANETS[planet_id]["levels"][lv]["mortgage"]
        del player.planets[planet_id]
        player.planet_exps.pop(planet_id, None)
        self._record_fund(player, cash, _lang.t("r_mortgage", name=_pname(PLANETS[planet_id])))
        self.message = _lang.t("msg_mortgage_ok", name=player.name,
                                planet=_pname(PLANETS[planet_id]), cash=cash)

        # 检查是否能还清过路费
        if self.pending_toll > 0:
            if player.funds >= self.pending_toll:
                self.confirm_pay_toll()   # 内部会调用 _maybe_show_fund_notice
            elif not player.planets:
                self._declare_bankrupt(player)
                self._maybe_show_fund_notice()
            # 否则继续等待交公
        else:
            # 惩罚格场景：经费转正后结束回合，否则继续交公
            if player.funds >= 0:
                self._end_turn_or_extra()
            self._maybe_show_fund_notice()

    def _declare_bankrupt(self, player: Player):
        player.bankrupt = True
        player.planets  = {}     # 释放所有星球，变为无主
        player.planet_exps = {}
        self.message = _lang.t("msg_bankrupt", name=player.name)
        self.phase    = GamePhase.BANKRUPT
        remaining = self.active_players
        if len(remaining) == 1:
            self.phase   = GamePhase.GAME_OVER
            self.message = _lang.t("msg_game_over", name=remaining[0].name)

    # ── 卡牌 ─────────────────────
    def _draw_event(self, player: Player) -> str:
        if not self.event_deck:
            self._setup_card_decks()
        card = dict(self.event_deck.pop())
        card["_type"] = "event"
        self.current_card = card
        self.phase   = GamePhase.CARD
        card_name = card.get("name_en", card["name"]) if _lang.is_en() else card["name"]
        card_desc = card.get("desc_en", card["desc"]) if _lang.is_en() else card["desc"]
        self.message = _lang.t("msg_card_event", name=player.name, card=card_name, desc=card_desc)
        return "event"

    def _draw_chance(self, player: Player) -> str:
        if not self.chance_deck:
            self._setup_card_decks()
        card = dict(self.chance_deck.pop())
        card["_type"] = "chance"
        self.current_card = card
        self.phase   = GamePhase.CARD
        card_name = card.get("name_en", card["name"]) if _lang.is_en() else card["name"]
        card_desc = card.get("desc_en", card["desc"]) if _lang.is_en() else card["desc"]
        self.message = _lang.t("msg_card_chance", name=player.name, card=card_name, desc=card_desc)
        return "chance"

    def apply_card_chance(self, choice: str):
        """事件卡12'一次机会'：choice='roll'再投骰子，'draw'抽机会卡"""
        self.current_card = None
        player = self.current_player
        if choice == "roll":
            self.extra_roll = True
            self.message = _lang.t("msg_chance_roll", name=player.name)
            self._end_turn_or_extra()
        else:
            self.message = _lang.t("msg_chance_draw", name=player.name)
            self._draw_chance(player)

    def apply_card(self):
        """确认应用当前展示的卡片效果"""
        card   = self.current_card
        player = self.current_player
        if card is None:
            self._end_turn_or_extra()
            return

        action = card["action"]

        if action == "none":
            pass   # 无效果，直接结束回合

        elif action == "fund":
            amt = card["amount"]
            card_nm = card.get("name_en", card["name"]) if _lang.is_en() else card["name"]
            s = "+" if amt > 0 else ""
            if amt > 0:
                player.earn(amt)
                self._record_fund(player, amt, _lang.t("r_card", name=card_nm))
            else:
                player.pay(abs(amt))
                self._record_fund(player, -abs(amt), _lang.t("r_card", name=card_nm))
            self.message += _lang.t("msg_fund_delta", s=s, amt=amt)

        elif action == "all_fund":
            amt = card["amount"]
            card_nm = card.get("name_en", card["name"]) if _lang.is_en() else card["name"]
            s = "+" if amt > 0 else ""
            for p in self.active_players:
                if amt > 0:
                    p.earn(amt)
                    self._record_fund(p, amt, _lang.t("r_card", name=card_nm))
                else:
                    p.pay(abs(amt))
                    self._record_fund(p, -abs(amt), _lang.t("r_card", name=card_nm))
            if card.get("extra") == "teleport":
                player.teleport(card["cell"])
            self.message += _lang.t("msg_all_fund", s=s, amt=amt)

        elif action == "teleport":
            player.teleport(card["cell"])
            self.message += _lang.t("msg_teleport_to", cell=_cname(BOARD[card["cell"]]))
            self.current_card = None
            self._handle_cell(player)
            self._maybe_show_fund_notice()
            return

        elif action == "reverse":
            player.reverse = True
            self.message += _lang.t("msg_reverse")

        elif action == "move":
            steps = card["steps"]
            if steps == "reverse":
                steps = -self._last_steps
            if steps > 0:
                passed = player.move(steps)
                if passed > 0:
                    bonus = PASS_EARTH_BONUS * passed
                    player.earn(bonus)
                    self._record_fund(player, bonus, _lang.t("r_pass_move"))
                    self.message += _lang.t("msg_pass_earth", name=player.name, bonus=bonus)
            else:
                passed = self._move_backward(player, abs(steps))
                if passed > 0:
                    bonus = PASS_EARTH_BONUS * passed
                    player.earn(bonus)
                    self._record_fund(player, bonus, _lang.t("r_pass_move"))
                    self.message += _lang.t("msg_pass_earth", name=player.name, bonus=bonus)
            self.message += _lang.t("msg_moved", steps=steps)
            self.current_card = None
            self._handle_cell(player)
            self._maybe_show_fund_notice()
            return

        elif action == "jail":
            player.jailed = 1
            player.jailed_reason = "jail"
            player.teleport(16)
            self.message += _lang.t("msg_jail_card")

        elif action == "extra_roll":
            self.extra_roll = True
            self.message += _lang.t("msg_extra_roll")

        elif action == "draw_chance":
            self.current_card = None
            self._draw_chance(player)
            return   # 新卡片无资金变化

        elif action == "keep":
            if player.keep_cards >= 1:
                self.message += _lang.t("msg_keep_full")
            else:
                player.keep_cards = 1
                self.message += _lang.t("msg_keep_ok")

        elif action == "lab":
            player.teleport(24)
            self.current_card = None
            self.phase   = GamePhase.LAB
            self.message = _lang.t("msg_lab_teleport", name=player.name)
            return

        elif action == "reposition":
            self.current_card = None
            self.start_reposition()
            return   # 不结束回合，等待玩家确认

        elif action == "skip_turn":
            player.jailed = 1   # 借用 jailed 计数原地停一轮（不移动到空间站）
            player.jailed_reason = "skip"
            self.message += _lang.t("msg_skip_next")

        elif action == "reset":
            player.teleport(0)
            player.funds = STARTING_FUNDS
            self.message += _lang.t("msg_reset", funds=STARTING_FUNDS)
            self.current_card = None
            self._handle_cell(player)
            self._maybe_show_fund_notice()
            return

        elif action == "comet_jail":
            stopped = []
            for p in self.active_players:
                if any(pid in COMET_PLANET_IDS for pid in p.planets):
                    p.jailed = 1
                    p.jailed_reason = "comet"
                    stopped.append(p.name)
            if stopped:
                self.message += _lang.t("msg_comet_jail", names=_lang.t("sep_comma").join(stopped))
            else:
                self.message += _lang.t("msg_comet_none")

        elif action == "give_fund":
            amt = abs(card["amount"])
            self.current_card = None
            others = [p for p in self.active_players if p.id != player.id]
            if others:
                self._give_fund_amt = amt
                self.phase   = GamePhase.GIVE_FUND
                self.message = _lang.t("msg_give_fund_q", amt=amt)
            else:
                self.message += _lang.t("msg_no_others")
                self._end_turn_or_extra()
                self._maybe_show_fund_notice()
            return

        elif action == "swap_planet":
            self.current_card = None
            others = [p for p in self.active_players if p.id != player.id and p.planets]
            if not others or not player.planets:
                self.message += _lang.t("msg_swap_no_planet")
                self._end_turn_or_extra()
                self._maybe_show_fund_notice()
            else:
                self._swap_target_id = -1
                self._swap_my_pid    = -1
                self.phase   = GamePhase.SWAP_PLAYER
                self.message = _lang.t("msg_swap_q")
            return

        elif action == "explore_free":
            unclaimed = self.get_unclaimed_planet_list()
            self.current_card = None
            if unclaimed:
                self.phase = GamePhase.EXPLORE_FREE
                self.message = _lang.t("msg_explore_free")
                return
            else:
                self.message += _lang.t("msg_explore_none")

        self.current_card = None
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    def _move_backward(self, player, steps):
        """反向移动，返回经过地球次数"""
        old_reverse = player.reverse
        player.reverse = True
        passed = player.move(steps)
        player.reverse = old_reverse
        return passed

    # ── 分享财富 ─────────────────
    def confirm_give_fund(self, target_id: int):
        """当前玩家向 target_id 玩家支付 _give_fund_amt 经费"""
        player = self.current_player
        target = self.players[target_id]
        amt    = self._give_fund_amt
        self._give_fund_amt = 0
        if player.pay(amt):
            target.earn(amt)
            self._record_fund(player, -amt, _lang.t("r_share"))
            self._record_fund(target, +amt, _lang.t("r_share"))
            self.message = _lang.t("msg_give_ok", name=player.name, target=target.name, amt=amt)
        else:
            self.message = _lang.t("msg_give_fail", name=player.name)
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    # ── 互换星球 ─────────────────
    def confirm_swap_target(self, target_id: int):
        """互换第1步：确认目标玩家，进入选自己星球"""
        self._swap_target_id = target_id
        self.phase   = GamePhase.SWAP_MINE
        self.message = _lang.t("msg_swap_mine", target=self.players[target_id].name)

    def confirm_swap_my_planet(self, my_pid: int):
        """互换第2步：确认自己给出的星球，进入选对方星球"""
        self._swap_my_pid = my_pid
        target = self.players[self._swap_target_id]
        self.phase   = GamePhase.SWAP_THEIRS
        self.message = _lang.t("msg_swap_theirs", target=target.name)

    def confirm_swap_complete(self, their_pid: int):
        """互换第3步：完成星球互换"""
        player = self.current_player
        target = self.players[self._swap_target_id]
        my_pid = self._swap_my_pid
        if my_pid not in player.planets or their_pid not in target.planets:
            self.message = _lang.t("msg_swap_cancel")
        else:
            lv_mine   = player.planets.pop(my_pid)
            lv_theirs = target.planets.pop(their_pid)
            player.planets[their_pid] = lv_theirs
            target.planets[my_pid]    = lv_mine
            exps_mine   = player.planet_exps.pop(my_pid, [False, False, False])
            exps_theirs = target.planet_exps.pop(their_pid, [False, False, False])
            player.planet_exps[their_pid] = exps_theirs
            target.planet_exps[my_pid]    = exps_mine
            self.message = _lang.t("msg_swap_ok",
                                   name=player.name, target=target.name,
                                   p1=_pname(PLANETS[my_pid]),
                                   p2=_pname(PLANETS[their_pid]))
        self._swap_target_id = -1
        self._swap_my_pid    = -1
        self._end_turn_or_extra()

    # ── 太空实验室 ───────────────
    _EXP_NAMES = ["采集矿物", "水实验", "植物实验"]

    def get_planet_exp_types(self, planet_id: int):
        """返回该星球当前玩家还未完成的实验类型索引列表（0=矿物,1=水,2=植物）"""
        exps = PLANETS.get(planet_id, {}).get("experiments", [])
        done = self.current_player.planet_exps.get(planet_id, [False, False, False])
        return [i for i, v in enumerate(exps) if v and not done[i]]

    def get_all_exp_types(self, planet_id: int):
        """返回该星球支持的所有实验类型（含已完成的）"""
        exps = PLANETS.get(planet_id, {}).get("experiments", [])
        return [i for i, v in enumerate(exps) if v]

    def do_experiment(self, planet_id: int, exp_type: int = -1):
        """在指定星球做实验：免费升到下一级（跳过探索费，跳过空白等级）"""
        player = self.current_player
        if planet_id not in player.planets:
            self._end_turn_or_extra()
            return
        pid   = planet_id
        lv    = player.planets[pid]
        pdata = PLANETS[pid]
        exp_nm = _lang.exp_name(exp_type) if 0 <= exp_type <= 2 else ("Experiment" if _lang.is_en() else "实验")
        # 检查该实验是否已完成
        if 0 <= exp_type <= 2 and player.planet_exps.get(pid, [False]*3)[exp_type]:
            self.message = _lang.t("msg_exp_done", planet=_pname(pdata), exp=exp_nm)
            self._end_turn_or_extra()
            return
        if not any(pdata["experiments"]):
            self.message = _lang.t("msg_exp_no", planet=_pname(pdata))
        elif lv >= 3:
            self.message = _lang.t("msg_exp_max", planet=_pname(pdata))
        else:
            next_lv = self._next_upgrade_level(pid, lv)
            if next_lv is None:
                self.message = _lang.t("msg_exp_max", planet=_pname(pdata))
            else:
                player.planets[pid] = next_lv
                if 0 <= exp_type <= 2:
                    player.planet_exps.setdefault(pid, [False, False, False])[exp_type] = True
                old_toll = pdata["levels"][lv]["toll"]
                new_toll = pdata["levels"][next_lv]["toll"]
                self.message = _lang.t("msg_exp_ok",
                                       name=player.name, planet=_pname(pdata),
                                       exp=exp_nm, lv=next_lv+1,
                                       old=old_toll, new=new_toll)
        self._end_turn_or_extra()

    def skip_lab(self):
        """跳过太空实验室"""
        self._end_turn_or_extra()

    # ── 调配探索者 ───────────────
    def start_reposition(self):
        """进入调配探索者阶段：当前玩家可拖动其他玩家棋子，共3次"""
        self._reposition_moves = 3
        self.phase   = GamePhase.REPOSITION
        self.message = _lang.t("msg_reposition", name=self.current_player.name)

    def reposition_move(self, player_id: int, cell: int) -> bool:
        """将 player_id 玩家移到 cell，消耗1次机会。返回是否成功"""
        if self._reposition_moves <= 0:
            return False
        if player_id == self.current_player.id:
            return False
        player = self.players[player_id]
        if player.bankrupt or player.pos == cell:
            return False
        player.pos = cell
        self._reposition_moves -= 1
        self.message = _lang.t("msg_reposition_move",
                               player=player.name,
                               cell=_cname(BOARD[cell]),
                               n=self._reposition_moves)
        return True

    def confirm_reposition(self):
        """确认调配，结束阶段"""
        self._reposition_moves = 0
        self.current_card = None
        self._end_turn_or_extra()

    # ── 调试工具 ──────────────────
    def _debug_reset(self):
        """调试跳转前重置临时状态"""
        self.current_card = None
        self._reposition_moves = 0
        self.phase = GamePhase.ROLL

    def debug_advance(self, steps: int):
        """调试：当前玩家前进 steps 格，触发格子效果"""
        self._debug_reset()
        player = self.current_player
        player.move(max(1, steps))
        self._handle_cell(player)

    def debug_goto_next(self, cell_type: str):
        """调试：传送当前玩家到下一个指定类型的格子"""
        self._debug_reset()
        player = self.current_player
        n = len(BOARD)
        for i in range(1, n):
            nxt = (player.pos + i) % n
            if BOARD[nxt]["type"] == cell_type:
                player.teleport(nxt)
                self._handle_cell(player)
                return

    # ── 收购 ──────────────────────
    def confirm_trade(self):
        """玩家选择收购当前落脚星球"""
        player = self.current_player
        pid    = self.pending_pid
        if pid < 0:
            self._end_turn_or_extra()
            return
        owner = self._find_planet_owner(pid)
        if owner is None or owner.id == player.id:
            self._end_turn_or_extra()
            return
        lv = owner.planets[pid]
        trade_cost = PLANETS[pid]["levels"][lv]["trade"]
        if player.pay(trade_cost):
            owner.earn(trade_cost)
            self._record_fund(player, -trade_cost, _lang.t("r_trade_buy", name=_pname(PLANETS[pid])))
            self._record_fund(owner,  +trade_cost, _lang.t("r_trade_sell", name=_pname(PLANETS[pid])))
            del owner.planets[pid]
            owner.planet_exps.pop(pid, None)
            player.planets[pid] = lv
            player.planet_exps[pid] = [False, False, False]
            self.message = _lang.t("msg_trade_ok",
                                   name=player.name, cost=trade_cost,
                                   planet=_pname(PLANETS[pid]))
        else:
            self.message = _lang.t("msg_trade_fail", name=player.name)
        self.pending_pid = -1
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    def skip_trade(self):
        """跳过收购"""
        self.pending_pid = -1
        self._end_turn_or_extra()

    # ── 精确落地球免费升级 ──────────
    def do_earth_upgrade(self, planet_id: int):
        """精确踏上地球后，免费升级指定星球"""
        player = self.current_player
        if planet_id not in player.planets:
            self._end_turn_or_extra()
            return
        lv = player.planets[planet_id]
        next_lv = self._next_upgrade_level(planet_id, lv)
        if next_lv is None:
            self.message = _lang.t("msg_earth_up_max",
                                   planet=_pname(PLANETS[planet_id]))
        else:
            player.planets[planet_id] = next_lv
            new_toll = PLANETS[planet_id]["levels"][next_lv]["toll"]
            self.message = _lang.t("msg_earth_up_ok",
                                   name=player.name, planet=_pname(PLANETS[planet_id]),
                                   lv=next_lv+1, toll=new_toll)
        self._end_turn_or_extra()

    def skip_earth_upgrade(self):
        """跳过地球免费升级"""
        self._end_turn_or_extra()

    # ── 回合结束 ─────────────────
    def _end_turn_or_extra(self):
        if self.extra_roll:
            self.extra_roll = False
            self.phase  = GamePhase.ROLL
            self.message += _lang.t("msg_extra_roll_turn")
        else:
            self._next_player()

    def _next_player(self):
        alive = [p for p in self.players if not p.bankrupt]
        if len(alive) <= 1:
            self.phase = GamePhase.GAME_OVER
            winner = alive[0] if alive else None
            self.message = _lang.t("msg_game_over",
                                   name=winner.name if winner else "?")
            return
        # 清理待处理状态
        self.pending_toll = 0
        self.pending_to   = -1
        self.pending_pid  = -1
        # 找下一位未破产玩家
        n = len(self.players)
        idx = (self.current_idx + 1) % n
        while self.players[idx].bankrupt:
            idx = (idx + 1) % n
        self.current_idx = idx
        player = self.current_player
        self.phase = GamePhase.ROLL
        # 处理停走
        if player.jailed > 0:
            player.jailed -= 1
            r_key = player.jailed_reason or "skip"
            reason = _lang.t(f"reason_{r_key}")
            player.jailed_reason = ""
            self.phase   = GamePhase.SKIP_NOTICE
            self.message = _lang.t("msg_skip_notice", reason=reason, name=player.name)
        else:
            self.message = _lang.t("msg_turn_start", name=player.name)

    def confirm_skip_notice(self):
        """玩家确认停走通知，切到下一位"""
        self._next_player()

    def _check_mortgage(self, player: Player):
        """检查玩家是否需要交公"""
        if player.funds < 0:
            player.funds = 0
            if player.planets:
                self.phase   = GamePhase.MORTGAGE
                self.message += _lang.t("msg_broke_mortgage")
            else:
                self._declare_bankrupt(player)
        else:
            self._end_turn_or_extra()

    # ── 工具 ─────────────────────
    def get_unclaimed_planet_list(self):
        """返回所有未被任何玩家探索的星球列表，格式与 get_player_planet_list 相同"""
        owned = set()
        for p in self.players:
            if not p.bankrupt:
                owned.update(p.planets.keys())
        result = []
        for pid, pdata in PLANETS.items():
            if pid not in owned:
                lv_data = pdata["levels"][0]
                result.append({
                    "planet_id": pid,
                    "name":      pdata["name"],
                    "name_en":   pdata.get("name_en", ""),
                    "level":     0,
                    "explore":   lv_data["explore"],
                    "toll":      lv_data["toll"],
                    "trade":     lv_data["trade"],
                    "mortgage":  lv_data["mortgage"],
                    "can_exp":   False,
                    "upgrade":   0,
                })
        return result

    def confirm_explore_free(self, planet_id: int):
        """免费探索指定星球（机会卡4效果）"""
        owned = set()
        for p in self.players:
            if not p.bankrupt:
                owned.update(p.planets.keys())
        player = self.current_player
        if planet_id in PLANETS and planet_id not in owned:
            player.planets[planet_id] = 0
            player.planet_exps[planet_id] = [False, False, False]
            self.message = _lang.t("msg_explore_free_ok",
                                   name=player.name, planet=_pname(PLANETS[planet_id]))
        else:
            self.message = _lang.t("msg_explore_free_no")
        self._end_turn_or_extra()
        self._maybe_show_fund_notice()

    def get_player_planet_list(self, player: Player):
        """返回玩家拥有的星球列表，用于 UI 显示"""
        result = []
        for pid, lv in player.planets.items():
            pdata = PLANETS[pid]
            lv_data = pdata["levels"][lv]
            next_real = self._next_upgrade_level(pid, lv)
            upgrade = PLANETS[pid]["levels"][next_real]["explore"] if next_real is not None else 0
            done = player.planet_exps.get(pid, [False, False, False])
            undone_exps = [i for i, (v, d) in enumerate(zip(pdata["experiments"], done)) if v and not d]
            can_exp = len(undone_exps) > 0 and lv < 3
            has_exp = any(pdata["experiments"])  # 是否支持任何实验（含已完成的）
            result.append({
                "planet_id": pid,
                "name":      pdata["name"],
                "name_en":   pdata.get("name_en", ""),
                "level":     lv,
                "explore":   lv_data["explore"],
                "toll":      lv_data["toll"],
                "trade":     lv_data["trade"],
                "mortgage":  lv_data["mortgage"],
                "can_exp":   can_exp,
                "has_exp":   has_exp,
                "upgrade":   upgrade,
            })
        return result
