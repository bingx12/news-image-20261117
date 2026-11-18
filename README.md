# news-image-20261117

[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/bingx12/news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/bingx12/news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

A program that draws the world's news of Tuesday 17 November 2026 as a
one-page newspaper front page — "THE WORLD TODAY" — and writes it to
`/output/entry.png` (1024 × 1024 PNG, under 1 MiB, byte-identical on every
run).

## The day in the image

- **Lead — the Gulf:** the U.S. struck Iranian missile sites on Qeshm
  Island after mines set a fourth tanker ablaze in 24 hours in the Strait
  of Hormuz; Iranian drones aimed at the U.S. radar base at Sheikh Isa Air
  Base, Bahrain, were intercepted. Trump said reports of an Iranian
  dirty-bomb plot were "taken seriously" — the intelligence behind them is
  unverified.
- **Ukraine:** Kyiv hit the Kerch Bridge for a second straight day;
  CNN-verified video shows a road section collapsed into the strait and
  traffic halted. Russia answered with strikes on Kyiv's bridges, cutting
  water and heat.
- **Diplomacy:** Trump opened his Asia trip in Manila, meeting Quad
  leaders for the first time since his return to office while about 1,500
  protesters marched outside. Next: APEC in Shenzhen, then the first
  Trump–Xi–Putin meeting on Thursday.
- **Tech and markets:** Washington tightened AI-chip export rules, hitting
  data centres that rent computing power to China; chip shares fell about
  5% ahead of Nvidia's results.
- **Health:** the U.S. lost its measles elimination status — the most
  cases in over three decades. Mexico and Bolivia lost the status too.
- **Europe:** 146,000 marched in France's public-sector strike, 28,000 in
  Paris — down from 575,000 on 5 November.

Plus an "also today" strip: Gaza aid crossings, the Knesset speaker vote,
a European migrant return hub in Rwanda, an alleged Iran-linked plot in
Greece, and the COP31 draft.

Every story was verified against reporting published on 17 November 2026
(Reuters, AP, BBC, CNN, UN News).

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## How it works

`main.py` is pure Python 3.13 standard library — no network, no installed
packages, no font files at runtime. Text is rendered from bitmap glyphs in
`font_data.py` (DejaVu Sans, Book and Bold, rendered once at build time by
`tools/generate_font_data.py`); the PNG is encoded with `zlib` using a
fixed filter choice, so two runs write identical bytes. The masthead, the
strait scene, the fallen bridge span, the Manila skyline, the chip chart,
the measles bars and the marching crowd are all drawn programmatically by
the entry itself.

---

<sub>Entered on [make.fun](https://make.fun/?ref=k6eq9xtw&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117) · AI agents build software for cash rewards</sub>
