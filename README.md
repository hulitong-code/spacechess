# Space Chess: Cosmic Explorer
### 星际征途探索强手棋

A space-themed board game (Monopoly-style) built with Python + pygame — a reimplementation of an original Scratch project.

> **Story:** This game was originally created in Scratch by a kid. Now, as a Python learning project, the same game has been rebuilt from scratch (pun intended) with a full graphical interface.
>
> 原版由小朋友用 Scratch 制作，现在作为 Python 学习项目重新实现。

---

## Features

- **2–6 players** on a 32-space board with 19 unique planets
- **Dice animation** — watch the dice spin before landing
- **Planet exploration** — buy, upgrade (4 levels), and collect tolls
- **Space Lab experiments** — 3 experiment types (Mining / Water / Plant) that double tolls
- **Trading & mortgaging** — acquire rivals' planets or sell your own to stay afloat
- **28 cards** — 14 Event cards + 14 Chance cards with varied effects
- **Bilingual** — full Chinese / English support, switchable at any time
- **Background music** — toggle with `M`
- **Smooth token movement** — step-by-step animation across the board

---

## Game Rules (Quick Reference)

| Element | Detail |
|---|---|
| Starting funds | 200 per player |
| Pass Earth bonus | +20 funds |
| Land on Earth | +20 + free planet upgrade |
| Doubles | Roll again (3rd doubles in a row → Space Station) |
| Space Station | Skip next turn |
| Space Lab | Conduct one experiment on an owned planet |
| Habitable Zone | Roll again immediately |
| Bankruptcy | Can't pay even after mortgaging all planets → eliminated |
| Win condition | Last player standing, or highest net worth when another player goes bankrupt |

### Board Layout (32 spaces, clockwise)

```
← 顶行 (26-32) ←──────────────── 地球 (1) ────── 右列 (2-9) →
                                                          ↓
太空实验室 (25) ←────────── 底行 (10-17) ────────── 空间站 (17)
↑
左列 (18-24)
```

### Planet Levels

Each planet has 4 exploration levels. Upgrade by paying the explore fee or completing lab experiments (free upgrade).

| Level | Name | Upgrade Method |
|---|---|---|
| Lv1 | Observation | Buy the planet |
| Lv2 | Satellite Probe | Pay upgrade fee |
| Lv3 | Rover Probe | Pay upgrade fee |
| Lv4 | Full Exploration | Pay upgrade fee |

Lab experiments (Mining / Water / Plant) each grant a **free level-up** and double the planet's toll.

---

## Installation

**Requirements:** Python 3.8+ and pygame

```bash
pip install pygame
```

**Run the game:**

```bash
cd spacechess
python main.py
```

---

## Controls

| Input | Action |
|---|---|
| Mouse click | All main interactions (buttons, pickers, drag tokens) |
| `M` | Toggle background music on/off |
| `D` | Toggle debug cell index display |
| `ZH` / `EN` button | Switch language (bottom-right corner) |
| `Ctrl+G` | Debug: advance current player by N spaces (enter number, confirm with Enter) |
| `Ctrl+J` | Debug: jump to next Chance card space |
| `Ctrl+E` | Debug: jump to next Event card space |
| `Esc` | Cancel current picker / debug input |

---

## Project Structure

```
spacechess/
├── main.py               # Entry point — game loop, button handling, animation
├── src/
│   ├── game.py           # Game logic (Player, GameState, GamePhase)
│   ├── data.py           # All game data (board, planets, cards, colors)
│   ├── ui.py             # pygame rendering (board, panel, popups, animations)
│   └── lang.py           # Bilingual string table (zh/en)
├── data/
│   ├── 星球信息.md        # Planet descriptions, facts, experiment types, level costs
│   ├── 事件卡.md          # Event card reference
│   ├── 机会卡.md          # Chance card reference
│   └── 规则书.md          # Full rulebook
└── assets/
    ├── background/
    │   ├── board.png      # Chinese board image
    │   └── board_en.png   # English board image
    ├── planets/circles/   # Planet artwork (planet_1.jpg … planet_19.jpg)
    └── players/           # Player token images (player_0.png … player_5.png)
```

---

## Planet List

| ID | Chinese | English | Experiments |
|---|---|---|---|
| 1 | 金星 | Venus | Mining |
| 2 | 水星 | Mercury | Mining |
| 3 | 坦普尔一号彗星 | Temple 1 Comet | Mining, Water |
| 4 | 格利泽581g | Gliese 581g | Water, Plant |
| 5 | 哈雷彗星 | Halley's Comet | Mining |
| 6 | 比邻星 | Proxima Centauri | Plant |
| 7 | 冥王星 | Pluto | Mining |
| 8 | 天狼星 | Sirius | — |
| 9 | 海王星 | Neptune | Water |
| 10 | 天王星 | Uranus | Mining |
| 11 | 土卫六 | Titan | Water, Plant |
| 12 | 土卫二 | Enceladus | Water |
| 13 | 土星 | Saturn | — |
| 14 | 木卫二 | Europa | Water |
| 15 | 木星 | Jupiter | — |
| 16 | 艳后星 | Cleopatra | Mining |
| 17 | 谷神星 | Ceres | Mining, Water |
| 18 | 火星 | Mars | Mining, Plant |
| 19 | 月球 | Moon | Mining, Plant |

---

## Card Effects Summary

### Event Cards (事件卡)
| Card | Effect |
|---|---|
| Suspected Black Hole | Next roll moves backward |
| Head to Mars | Teleport to Mars |
| Reposition Explorers | Move other players up to 3 times |
| Retreat! | Return to starting position this turn |
| Planet Swap | Swap one planet with another player |
| Visit Space Lab | Teleport to lab, conduct experiment |
| Visit Space Station | Go to Space Station, skip next turn |
| Skip a Turn | Skip next turn |
| Comet Blackout | All comet planet owners skip a turn |
| Back to Earth | Return to Earth, funds reset to starting amount |
| Draw Chance Card | Draw a Chance card |
| Lucky Chance | Choose: roll again or draw Chance card |
| SOS | Keep card — use anytime to skip a toll |
| Surprise Find! | Move forward 5 spaces |

### Chance Cards (机会卡)
| Card | Effect |
|---|---|
| New Discovery? | Move back 5 spaces |
| Conquer Fear | Roll again |
| Don't Fear Mistakes | Return to Earth |
| Earth is Calling! | Free explore any unclaimed planet |
| Daily Exercise | Lose 10 funds |
| Share the Wealth | Give 30 funds to any player |
| Visit Space Lab | Teleport to lab, conduct experiment |
| Reward! | Gain 50 funds |
| No Talking While Eating | Lose 10 funds |
| Learn Humbly | Gain 30 funds |
| Space Nap | Skip a turn |
| Rigorous Training | Lose 50 funds |
| Share Fun Stories | Nothing happens |
| Visit Space Lab | Teleport to lab, conduct experiment |

---

## Credits

- **Original Scratch game:** [星际征途探索强手棋](https://scratch.mit.edu/projects/410981892/) by hufuzhipeng
- **Python reimplementation:** Family project — learning Python through rebuilding a childhood creation
