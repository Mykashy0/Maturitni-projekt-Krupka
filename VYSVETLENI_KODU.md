# Vysvětlení kódu – Astrallift

Tenhle soubor prochází **celý kód** projektu a vysvětluje, co která část dělá a proč.
Odkazy jako [hra.py:117](hra.py#L117) tě ve VS Code (v náhledu `Ctrl + Shift + V`)
nebo na GitHubu přenesou přímo na daný řádek. Čísla řádků platí pro verzi, ke které
byl tenhle popis napsaný – když kód změníš, můžou se trochu posunout.

**Obsah**

0. [Velký obrázek – jak to celé funguje](#0-velký-obrázek--jak-to-celé-funguje)
1. [Slovníček pojmů](#1-slovníček-pojmů)
2. [hra.py – hra](#2-hrapy--hra)
3. [web/app.py – web](#3-webapppy--web)
4. [HTML šablony (web/templates)](#4-html-šablony-webtemplates)
5. [CSS (web/static/styly.css)](#5-css-webstaticstylycss)
6. [Databáze](#6-databáze)
7. [Ostatní soubory](#7-ostatní-soubory)
8. [Jak udělat typické změny](#8-jak-udělat-typické-změny)
9. [Otázky, které můžou padnout u maturity](#9-otázky-které-můžou-padnout-u-maturity)

---

## 0. Velký obrázek – jak to celé funguje

Projekt má **tři části**, které spolu mluví:

```
   PROHLÍŽEČ                    WEB (web/app.py)                 DATABÁZE (MySQL)
 ┌───────────┐  klikne/odešle  ┌──────────────────┐   SQL dotazy  ┌──────────────────┐
 │  stránky  │ ──────────────► │  Flask: stránky, │ ────────────► │ ast_hraci        │
 │  .html    │ ◄────────────── │  login, výsledky │ ◄──────────── │ ast_hry          │
 └───────────┘   hotová HTML   └──────────────────┘    řádky      │ ast_predmety     │
                                      │ tlačítko Hrát             │ ast_odevzdane_.. │
                                      │ 1) zapíše jméno do         └──────────────────┘
                                      │    prihlaseny.txt                  ▲
                                      │ 2) spustí hra.py                    │
                                      ▼                                     │
                               ┌──────────────────┐  konec hry: INSERT      │
                               │  HRA (hra.py)    │ ────────────────────────┘
                               │  Pygame okno     │
                               └──────────────────┘
```

**Co se děje, když hráč hraje:**

1. Spustíš web (`python web/app.py`). Web si v databázi vytvoří tabulky (když ještě nejsou).
2. V prohlížeči se zaregistruješ → web uloží jméno a **hash** hesla do tabulky `ast_hraci`.
3. Klikneš na **▶ Hrát** → web zapíše tvoje jméno do souboru `prihlaseny.txt` a spustí `hra.py`.
4. Hra si při startu přečte `prihlaseny.txt` → ví, kdo hraje (a soubor vymaže).
5. Hraješ. Když dojde čas, hra uloží výsledek do tabulek `ast_hry` a `ast_odevzdane_predmety`.
6. Na webu na stránce **Výsledky** web přečte data z databáze a ukáže žebříček.

**Soubory:**

| Soubor | Co dělá |
|--------|---------|
| [hra.py](hra.py) | celá hra (okno, menu, nastavení, hraní, uložení skóre) |
| [web/app.py](web/app.py) | celý web (stránky, přihlášení, registrace, výsledky, spuštění hry) + všechno SQL |
| [web/templates/](web/templates/) | 4 HTML stránky (O hře, Výsledky, Autor, Přihlášení) |
| [web/static/styly.css](web/static/styly.css) | vzhled webu |
| `pripojeni.py` | adresa, jméno a heslo k databázi |
| `hudba.wav` | hudba ve hře |
| [requirements.txt](requirements.txt) | seznam knihoven, které se instalují přes `pip` |

---

## 1. Slovníček pojmů

### Python

| Pojem | Co to je | Příklad z projektu |
|-------|----------|--------------------|
| **proměnná** | „krabička“ s hodnotou | `zbyva = 60` |
| **konstanta** | proměnná, kterou neměníme; píše se VELKÝMI písmeny | `RYCHLOST_HRACE = 250` |
| **funkce** | pojmenovaný kus kódu, který můžeš zavolat; `return` vrátí výsledek | `def je_ruda(x, y): ...` |
| **seznam** (list) | řada hodnot v `[ ]`, čísluje se od 0 | `STAVBY = ["tezic", "pec", "lis", "pas"]` → `STAVBY[0]` je `"tezic"` |
| **2D seznam** | seznam seznamů = tabulka; `mapa[radek][sloupec]` | mapa hry |
| **n-tice** (tuple) | jako seznam, ale v `( )` a nedá se měnit | barva `(255, 90, 90)`, směr `(1, 0)` |
| **slovník** (dict) | dvojice **klíč: hodnota** v `{ }` | `BODY = {"ruda": 1, "ingot": 2, "plech": 4}` → `BODY["ingot"]` je `2` |
| **None** | „nic“, prázdná hodnota | prázdné políčko mapy je `None` |
| **podmínka** | `if` / `elif` / `else` | `if je_vytah(x, y): ...` |
| **cyklus for** | opakuj pro každou položku | `for stroj in stroje:` |
| **cyklus while** | opakuj, dokud platí podmínka | `while bezi:` (hlavní smyčka hry) |
| **try / except** | „zkus to, a když to spadne, udělej tohle“ – program pak nespadne | čtení souboru, databáze |
| **f-string** | text s proměnnými uvnitř `{ }` | `f"Body {skore}"` |
| **třída / objekt** | šablona (třída) a konkrétní věc z ní (objekt); `self` = „já sám“ | `class Tlacitko` → `tl_konec = Tlacitko("Konec", ...)` |
| **import** | načte knihovnu nebo jiný soubor | `import pygame` |
| **with open(...)** | otevře soubor a sám ho zase zavře | čtení `volby.txt` |

### Pygame (hra)

| Pojem | Co to je |
|-------|----------|
| **okno** (`okno`) | plocha, na kterou kreslíme |
| **snímek** (frame) | jedno překreslení obrazovky; hra jich dělá 60 za sekundu (**FPS**) |
| **hlavní smyčka** | `while` cyklus, který se opakuje každý snímek: *1. vstupy → 2. logika → 3. kreslení* |
| **událost** (event) | něco, co udělal hráč: stisk klávesy, kliknutí, zavření okna |
| **dt** | kolik sekund uběhlo od minulého snímku (asi 0,016 s). Pohyb `rychlost * dt` je pak stejně rychlý na rychlém i pomalém PC |
| **Rect** | obdélník (x, y, šířka, výška); umí např. `collidepoint` = „je bod uvnitř?“ |
| **blit** | „nalep“ obrázek (třeba text) na okno |
| **flip** | ukaž, co jsme za tento snímek nakreslili |

### Flask (web)

| Pojem | Co to je |
|-------|----------|
| **route** | adresa stránky; `@app.route("/vysledky")` = tahle funkce obsluhuje adresu `/vysledky` |
| **GET / POST** | GET = otevření stránky, POST = odeslání formuláře |
| **render_template** | vezme HTML šablonu, doplní do ní proměnné a pošle ji prohlížeči |
| **request.form** | data z odeslaného formuláře (`request.form["jmeno"]`) |
| **request.args** | data z adresy za otazníkem (`/vysledky?hledat=pepa`) |
| **session** | „paměť“ pro přihlášeného uživatele (uložená v cookie v prohlížeči) |
| **redirect** | přesměruj prohlížeč na jinou stránku |
| **Jinja** | jazyk šablon: `{{ promenna }}` vypíše hodnotu, `{% if %}`, `{% for %}` |

### Databáze

| Pojem | Co to je |
|-------|----------|
| **tabulka** | jako tabulka v Excelu: sloupce = vlastnosti, řádky = záznamy |
| **PRIMARY KEY** | jednoznačné číslo řádku (`id`) |
| **AUTO_INCREMENT** | databáze sama přidělí další číslo |
| **FOREIGN KEY** | sloupec, který odkazuje na `id` v jiné tabulce |
| **1:N** | jeden hráč → mnoho her |
| **M:N** | mnoho her ↔ mnoho předmětů (potřebuje „vazební“ tabulku) |
| **SELECT / INSERT** | přečti data / vlož data |
| **JOIN** | spoj dvě tabulky podle společného sloupce |
| **WHERE / ORDER BY / GROUP BY / LIKE** | filtruj / seřaď / seskup / hledej podle části textu |
| **%s** | místo pro hodnotu v SQL dotazu – hodnotu doplní knihovna bezpečně (ochrana proti **SQL injection**) |
| **commit** | potvrď změny (bez něj se INSERT neuloží) |
| **hash hesla** | z hesla se vyrobí „otisk“, ze kterého heslo zpátky zjistit nejde. Do databáze se ukládá jen otisk (knihovna **bcrypt**) |

---

## 2. hra.py – hra

Celá hra je v jednom souboru, rozděleném na 8 částí (nadpisy `# ===== 1) ... =====`).
Python čte soubor odshora dolů: nejdřív si **definuje** konstanty a funkce (části 1–7)
a teprve na konci (část 8) se všechno **spustí** v hlavní smyčce.

### Začátek souboru ([hra.py:18](hra.py#L18))

```python
import os
import webbrowser
import pygame
import mysql.connector
```

- `os` – práce se složkami.
- `webbrowser` – otevře web v prohlížeči (tlačítko „Web – výsledky“).
- `pygame` – knihovna na hry (okno, kreslení, klávesy, myš, hudba).
- `mysql.connector` – připojení k databázi MySQL.

```python
try:
    from pripojeni import *
except ImportError:
    print("Chybí soubor pripojeni.py – skóre se nebude ukládat.")
```

Načte `HOST`, `USER`, `PASSWORD`, `DATABASE` ze souboru `pripojeni.py`.
Když soubor chybí, hra **nespadne** – jen vypíše hlášku a později se neuloží skóre.

```python
os.chdir(os.path.dirname(os.path.abspath(__file__)))
```

„Přepni se do složky, kde leží tento soubor.“ Díky tomu hra najde `hudba.wav`,
`volby.txt` a `prihlaseny.txt`, i když ji spustíš z jiné složky (třeba z webu).

---

### Část 1) Nastavení hry ([hra.py:35](hra.py#L35))

Tady jsou **jen čísla a texty**, které můžeš měnit. Nic se tu nepočítá.

**Okno a mapa:**

| Konstanta | Hodnota | Význam |
|-----------|---------|--------|
| `SIRKA`, `VYSKA` | 1280 × 720 | velikost okna v pixelech |
| `FPS` | 60 | snímků za sekundu |
| `DLAZDICE` | 40 | mapa je ze čtverečků 40 × 40 px |
| `LISTA` | 80 | výška horního pruhu (čas, body, inventář) |
| `SLOUPCU` | 32 | 1280 / 40 = 32 sloupců |
| `RADKU` | 16 | (720 − 80) / 40 = 16 řádků |

Mapa tedy vypadá takhle (sloupce 0–31, řádky 0–15):

```
 y=0  ┌────────────── horní lišta (80 px) ──────────────┐
      │                                                  │
 řádek 4 ┌─────┐                                         │
         │RUDA │  (sloupce 1–5, řádky 4–11)       ┌───┐  │ řádek 6
         │     │                                  │VÝT│  │ (sloupce 27–29,
         │     │                                  │AH │  │  řádky 6–9)
 řádek 11└─────┘                                  └───┘  │
      │                                                  │
      └──────────────────────────────────────────────────┘
```

**Převod pixelů na políčko:** `sloupec = x // 40`, `radek = (y − 80) // 40`
(`//` je celočíselné dělení, např. `130 // 40 = 3`).

**Hráč a web:** `RYCHLOST_HRACE = 250` (px za sekundu), `VELIKOST_HRACE = 28` (px),
`ADRESA_WEBU` = kam vede tlačítko „Web“.

**Ruda a výtah:** `RUDA_X, RUDA_Y, RUDA_SIRKA, RUDA_VYSKA` a `VYTAH_X, …` určují,
kde na mapě jsou (v políčkách).

**Body** ([hra.py:64](hra.py#L64)):
```python
BODY = {"ruda": 1, "ingot": 2, "plech": 4}
```
Kolik bodů je za kus. `BODY["plech"]` vrátí `4`.

**Stroje** ([hra.py:72](hra.py#L72)) – slovník slovníků. Pro každý stroj:

| Klíč | Těžič | Pec | Lis | Význam |
|------|-------|-----|-----|--------|
| `nazev` | Těžič | Pec | Lis | jméno pro hráče |
| `cena` | 5 | 10 | 15 | kolik rudy stojí postavení |
| `vstup` | `None` | ruda | ingot | co stroj spotřebuje (`None` = nic) |
| `vystup` | ruda | ingot | plech | co vyrobí |
| `doba` | 2 | 2 | 3 | za kolik sekund vyrobí 1 kus |
| `velikost` | 1 | 2 | 2 | 1 = stroj 1×1, 2 = stroj 2×1 |
| `barva` | oranžová | červená | modrá | barva (R, G, B) |

Takže `STROJE["pec"]["cena"]` je `10`.

**Další konstanty:**
- `MAX_ZASOBA = 20` – víc se do stroje nevejde (na vstup ani na výstup).
- `CENA_PASU = 1`, `RYCHLOST_PASU = 2` (políčka za sekundu).
- `KLAVESY_STAVEB` – slovník „klávesa → co se staví“ (`pygame.K_1` → `"tezic"` …).
- `STAVBY` – pořadí staveb v horní liště.
- **Směry** ([hra.py:90](hra.py#L90)):
  ```python
  SMERY = [(1, 0), (0, 1), (-1, 0), (0, -1)]   # 0 vpravo, 1 dolů, 2 vlevo, 3 nahoru
  ```
  Každý směr je dvojice „o kolik se posunout ve sloupcích a v řádcích“.
  Např. směr 0 = `(1, 0)` = o jeden sloupec doprava. Směr se ukládá jako **číslo** 0–3
  (pozice v seznamu), proto otočení o 90° je jen `smer = (smer + 1) % 4`.
- `SIPKY` – šipky k jednotlivým směrům (pro text v liště).
- `NAZVY_BAREV`, `BARVY_HRACE` – barvy, které si hráč může vybrat v nastavení.
- `BILA`, `SEDA`, … – pojmenované barvy, ať se v kódu nepíšou čísla.

---

### Část 2) Volby hráče ([hra.py:108](hra.py#L108))

**Volby** = to, co si hráč nastaví v menu **Nastavení**. Ukládají se do textového
souboru `volby.txt`, aby si je hra pamatovala i po vypnutí.

```python
volby = {"hudba": 50, "fps": 0, "mrizka": 1, "napoveda": 1, "cela": 0, "barva": 0}
```
Výchozí hodnoty. `1` = zapnuto, `0` = vypnuto, `hudba` = hlasitost 0–100 %,
`barva` = pořadí v seznamu `BARVY_HRACE` (0 = žlutá).

#### `nacti_volby()` ([hra.py:117](hra.py#L117))
Přečte `volby.txt` řádek po řádku. Řádek `hudba=60` rozdělí podle `=`:
```python
casti = radek.strip().split("=")     # "hudba=60\n" -> ["hudba", "60"]
volby[casti[0]] = int(casti[1])      # volby["hudba"] = 60
```
- `strip()` odstraní mezery a konec řádku, `split("=")` rozdělí text, `int()` udělá z textu číslo.
- Když soubor neexistuje (`FileNotFoundError`) nebo je v něm nesmysl (`ValueError`),
  zůstanou výchozí volby – hra nespadne.
- Nakonec pojistka: kdyby číslo barvy bylo moc velké, nastaví se 0.

#### `uloz_volby()` ([hra.py:131](hra.py#L131))
Zapíše každou volbu jako řádek `klic=hodnota` (režim `"w"` = přepiš soubor).
`volby.items()` dává dvojice (klíč, hodnota).

#### `zjisti_prihlaseneho_hrace()` ([hra.py:138](hra.py#L138))
Přečte jméno ze souboru `prihlaseny.txt` (zapsal ho tam web po kliknutí na Hrát)
a **soubor hned vymaže** (zapíše do něj prázdný text). Proč? Kdyby tam jméno zůstalo,
další hra spuštěná napřímo (bez webu) by se uložila pod tímto jménem.
Vrací jméno, nebo `""` (prázdný text) = nikdo není přihlášený.

---

### Část 3) Databáze – `uloz_do_databaze()` ([hra.py:159](hra.py#L159))

Zavolá se na konci hry. Dostane jméno hráče, délku hry, skóre a slovník
`odevzdano` (např. `{"ruda": 10, "ingot": 3, "plech": 0}`). Postup:

1. **Připojí se** k databázi (`mysql.connector.connect(...)`) a vytvoří **kurzor**
   (`mycursor`) – přes něj se posílají SQL příkazy.
2. **Najde id hráče:**
   `SELECT id FROM ast_hraci WHERE jmeno = %s` → `fetchone()` vrátí řádek, např. `(7,)`,
   a `[0]` z něj vezme první hodnotu → `7`.
3. **Uloží hru:** `INSERT INTO ast_hry (hrac_id, delka_minut, skore) VALUES (%s, %s, %s)`.
   Datum se doplní samo (`DEFAULT CURRENT_TIMESTAMP`).
4. **Zjistí id právě uložené hry:** `SELECT MAX(id) FROM ast_hry WHERE hrac_id = %s`
   (nejvyšší číslo hry tohoto hráče = ta nejnovější).
5. **Uloží, co se odeslalo:** pro každý předmět s počtem > 0 najde jeho `id`
   v `ast_predmety` a vloží řádek do `ast_odevzdane_predmety`.
6. `mydb.commit()` – **potvrdí** všechny změny. Bez commitu by se nic neuložilo.
7. Vrátí `True`.

Když cokoliv selže (databáze nejde, hráč neexistuje, chybí `pripojeni.py`),
`except Exception` chybu chytí, vypíše ji a funkce vrátí `False` → hra ukáže
„Výsledek se NEPODAŘILO uložit“, ale **nespadne**.

> **Proč `%s` a ne f-string?** Kdyby se jméno vkládalo přímo do textu dotazu,
> šlo by do jména napsat kus SQL příkazu (SQL injection). S `%s` knihovna hodnotu
> vloží bezpečně.

---

### Část 4) Hudba ([hra.py:196](hra.py#L196))

```python
pygame.init()                       # zapne pygame
pygame.mixer.init()                 # zapne zvuk
pygame.mixer.music.load("hudba.wav")
```
Je to v `try / except pygame.error` – na počítači bez zvukové karty hra pojede potichu
(`hudba_funguje = False`).

#### `nastav_hlasitost()` ([hra.py:210](hra.py#L210))
Pygame chce hlasitost od 0.0 do 1.0, my máme 0–100 %, proto `volby["hudba"] / 100`.

---

### Část 5) Tlačítko – třída `Tlacitko` ([hra.py:220](hra.py#L220))

Všechna tlačítka v menu jsou **objekty** této třídy.

- `__init__(self, text, x, y, sirka=360, vyska=50)` – spustí se při vytvoření tlačítka.
  Uloží si text a vytvoří obdélník (`pygame.Rect`), jehož **střed** je v bodě (x, y).
  `sirka` a `vyska` mají výchozí hodnoty – když je nezadáš, použijí se 360 a 50.
- `nakresli(self)` – nakreslí tlačítko. Když je myš nad ním
  (`self.rect.collidepoint(pygame.mouse.get_pos())`), použije světlejší barvu.
  Pak nakreslí rámeček a doprostřed napíše text.
- `kliknuto(self, udalost)` – vrátí `True`, když událost je **kliknutí levým tlačítkem**
  (`MOUSEBUTTONDOWN` a `button == 1`) a místo kliknutí je uvnitř tlačítka.

Použití: `tl_konec = Tlacitko("Konec", 640, 610)` a v hlavní smyčce
`if tl_konec.kliknuto(udalost): ...`.

---

### Část 6) Mapa a stavění – herní logika ([hra.py:246](hra.py#L246))

#### Jak je uložená mapa

`mapa` je **2D seznam** (16 řádků × 32 sloupců). Na políčko se sáhne `mapa[y][x]`
(nejdřív řádek, pak sloupec). Na každém políčku je:

- `None` – nic tam nestojí,
- **pás** – slovník:
  ```python
  {"druh": "pas", "smer": 0, "predmet": "ruda", "posun": 0.4}
  ```
  `predmet` = co na pásu leží (`None` = nic), `posun` = jak daleko věc dojela
  (0 = začátek políčka, 1 = konec),
- **stroj** – slovník:
  ```python
  {"druh": "pec", "x": 4, "y": 6, "smer": 0, "vstup": 3, "hotovo": 1, "cas": 0.7, "pracuje": True}
  ```
  `x, y` = první políčko stroje, `vstup` = kolik surovin čeká, `hotovo` = kolik výrobků
  čeká na odeslání, `cas` = jak dlouho už vyrábí další kus, `pracuje` = jestli zrovna vyrábí.

Stroj 2×1 (pec, lis) zabírá **dvě políčka a na obou je ten samý slovník**.
Ať klikneš na kteroukoliv polovinu, je to ten samý stroj. Kromě mapy jsou všechny
stroje ještě v seznamu `stroje` – aby se daly jednoduše projít cyklem `for`.

#### Pomocné funkce

| Funkce | Řádek | Co dělá |
|--------|-------|---------|
| `je_ruda(x, y)` | [257](hra.py#L257) | `True`, když políčko leží v ložisku rudy |
| `je_vytah(x, y)` | [262](hra.py#L262) | `True`, když políčko je výtah |
| `je_na_mape(x, y)` | [267](hra.py#L267) | `True`, když políčko není mimo mapu |
| `nova_mapa()` | [272](hra.py#L272) | vytvoří prázdnou mapu: 16× přidá řádek `[None] * 32` |
| `spocitej_body(predmety)` | [280](hra.py#L280) | sečte body: `{"ruda": 3, "ingot": 1}` → 3·1 + 1·2 = **5** |

`je_ruda` používá dvojité porovnání `RUDA_X <= x < RUDA_X + RUDA_SIRKA`
= „x je od 1 do 5“.

#### `policka_stavby(druh, x, y, smer_stavby)` ([hra.py:288](hra.py#L288))
Vrátí seznam políček, která stavba zabere.
- Pás a těžič: jen `[(x, y)]`.
- Pec a lis (velikost 2): `[(x, y), (x + dx, y + dy)]`, kde `(dx, dy)` je směr.
  Příklad: pec na (4, 6) otočená doprava (`(1, 0)`) → `[(4, 6), (5, 6)]`.
  Otočená dolů (`(0, 1)`) → `[(4, 6), (4, 7)]`.
  **První políčko je vstupní, druhé výstupní.**

#### `proc_nejde_stavet(druh, x, y)` ([hra.py:296](hra.py#L296))
Postupně kontroluje, jestli se dá stavět. Vrátí **důvod** (text), nebo `""`, když je vše OK:
1. každé políčko stavby musí být na mapě, nesmí to být výtah a nesmí tam nic stát,
2. těžič musí stát na rudě,
3. hráč musí mít dost rudy.

Stejná funkce se používá i pro **náhled** (zelený/červený rámeček pod myší).

#### `postav(druh, x, y)` ([hra.py:316](hra.py#L316))
Odečte rudu a postaví:
- **pás** → na políčko dá nový slovník pásu,
- **stroj** → vytvoří slovník stroje, přidá ho do seznamu `stroje`
  a dá ho na všechna jeho políčka.

Směr stavby se bere z proměnné `smer` (otáčí se klávesou R).

#### `zbourej(x, y)` ([hra.py:330](hra.py#L330))
Vrátí hráči rudu (cenu stavby) a všechno, co bylo uvnitř (věc na pásu, suroviny
a výrobky ve stroji). Pak políčka vyprázdní (`None`) a stroj vyřadí ze seznamu `stroje`.

#### `vloz_predmet(x, y, predmet)` ([hra.py:355](hra.py#L355)) – nejdůležitější funkce továrny
Zkusí dát **jeden** předmět na políčko (x, y). Vrátí `True`, když ho tam něco vzalo:
- **výtah** → předmět „odletí“: `odevzdano[predmet] += 1` (tím přibudou body),
- **prázdný pás** → položí ho na začátek pásu (`posun = 0`),
- **stroj** → vezme ho, jen když je to jeho surovina a má místo (`vstup < MAX_ZASOBA`).

Jinak vrátí `False` (věc zůstane tam, kde byla, a zkusí to příští snímek).
Tuhle funkci používají stroje i pásy – díky tomu umí pás vozit věci do strojů,
do dalších pásů i do výtahu.

#### `aktualizuj_stroje(dt)` ([hra.py:383](hra.py#L383))
Volá se každý snímek. Pro každý stroj:
1. **Výroba:** stroj pracuje, když má suroviny (těžič je nepotřebuje) a má kam dát výrobek.
   K `cas` přičte `dt`. Když `cas` dosáhne `doba` (např. 2 s), vynuluje se,
   spotřebuje se 1 surovina a přibude 1 hotový výrobek.
2. **Odeslání:** když má hotové výrobky, zkusí jeden dát (`vloz_predmet`) na políčko
   **za výstupní stranou** stroje (poslední políčko stroje + směr).

#### `aktualizuj_pasy(dt)` ([hra.py:407](hra.py#L407))
Projde celou mapu (dva vnořené cykly `for y` a `for x`). Na každém pásu s věcí
zvětší `posun` o `RYCHLOST_PASU * dt`. Když `posun` dojde na 1 (konec políčka),
zkusí věc předat na další políčko ve směru pásu. Když to nejde (další pás je plný),
věc na konci počká.

**Cesta jedné rudy továrnou:**
```
těžič vyrobí rudu → vloz_predmet na pás vpravo → pás ji veze (posun 0 → 1)
→ vloz_predmet na další pás → … → vloz_predmet do pece (vstup +1)
→ pec za 2 s udělá ingot → vloz_predmet na pás → … → výtah → odevzdano["ingot"] += 1 → +2 body
```

#### `stiskni_e(x, y)` ([hra.py:423](hra.py#L423))
Co udělá klávesa E na políčku, kde stojí hráč. Kontroluje v tomhle pořadí:
1. **výtah** → odešle vše z inventáře (přičte do `odevzdano`, inventář vynuluje),
2. **pás** → sebere věc z pásu do inventáře,
3. **stroj** → vezme hotové výrobky a vloží do něj suroviny (jen kolik se vejde – `min(...)`),
4. **ruda** → +1 ruda do inventáře,
5. jinak → „Tady nic není…“.

Vrací text zprávy, který se ukáže dole na obrazovce.

---

### Část 7) Kreslení ([hra.py:468](hra.py#L468))

Kreslí se pořád dokola, 60× za sekundu, celé znovu. Pořadí kreslení je důležité –
co se nakreslí později, je **navrchu**.

| Funkce | Řádek | Co kreslí |
|--------|-------|-----------|
| `napis(text, font, barva, stred)` | [472](hra.py#L472) | text vycentrovaný na bod `stred` (`render` udělá z textu obrázek, `blit` ho nalepí) |
| `stred_policka(x, y)` | [478](hra.py#L478) | vrátí střed políčka v pixelech: `x·40 + 20`, `80 + y·40 + 20` |
| `nakresli_predmet(nazev, x, y)` | [483](hra.py#L483) | ikonku: ruda = hnědé kolečko, ingot = šedý obdélníček, plech = světlý čtvereček |
| `nakresli_sipku(x, y, smer, barva)` | [496](hra.py#L496) | trojúhelníkovou šipku daným směrem |
| `nakresli_mapu()` | [506](hra.py#L506) | všechna políčka (zem / ruda / výtah), mřížku, žlutý rám výtahu, paprsek, blikající světlo, popisky |
| `nakresli_pasy()` | [535](hra.py#L535) | pásy se šipkou a věci na nich |
| `nakresli_stroje()` | [553](hra.py#L553) | stroje: obdélník, počty, vrták, zelený proužek výroby, bílou šipku výstupu |
| `nakresli_nahled(druh, x, y)` | [601](hra.py#L601) | zelený/červený rámeček pod myší (jde / nejde stavět) |
| `nakresli_hrace()` | [615](hra.py#L615) | hráče (čtverec s očima) a bílý rámeček políčka, kde stojí |
| `nakresli_listu()` | [627](hra.py#L627) | horní pruh: čas, body, inventář, stavby 1–4, směr, FPS |
| `nakresli_spodek()` | [666](hra.py#L666) | dole zprávu pro hráče a řádek s nápovědou |

**Zajímavé detaily:**

- **Šipka** (`nakresli_sipku`): `(dx, dy)` je směr šipky, `(-dy, dx)` je směr otočený
  o 90° („do boku“). Špička je kus dopředu, dva rohy kus dozadu a do stran →
  `pygame.draw.polygon` nakreslí trojúhelník.
- **Věc na pásu** (`nakresli_pasy`): pozice = střed políčka + směr · (posun − 0,5) · 40.
  Při `posun = 0` je věc na začátku políčka, při `0.5` uprostřed, při `1` na konci.
- **Stroj 2×1** (`nakresli_stroje`): obdélník přes obě políčka se spočítá z menšího
  ze dvou sloupců/řádků (`min`) a z rozdílu (`abs(x2 - x1) + 1` políček).
- **Animace** bez složité matematiky: `pygame.time.get_ticks()` vrací milisekundy od
  startu. `get_ticks() // 150 % 2` se každých 150 ms přepíná mezi 0 a 1 → vrták střídá
  tvar „+“ a „×“, světlo výtahu bliká (500 ms).
- **Čas** v liště: `f"{sekundy // 60}:{sekundy % 60:02d}"` → `:02d` doplní nulu (`1:05`).
  Posledních 10 sekund je čas červený.

---

### Část 8) Hlavní smyčka ([hra.py:681](hra.py#L681))

#### Příprava (spustí se jednou)

1. `nacti_volby()`, `nastav_hlasitost()`, hudba začne hrát dokola (`play(-1)`).
2. `otevri_okno()` ([hra.py:691](hra.py#L691)) – otevře okno normálně, nebo přes celou
   obrazovku (`pygame.FULLSCREEN`), podle voleb.
3. Nastaví titulek okna, `hodiny` (pro FPS) a 4 velikosti písma (`font_...`).
4. `jmeno_hrace = zjisti_prihlaseneho_hrace()` – kdo hraje.
5. Vytvoří všechna **tlačítka** (menu, nastavení, konec hry) ([hra.py:709](hra.py#L709)).
6. Připraví **proměnné hry** ([hra.py:732](hra.py#L732)): mapa, stroje, inventář,
   odevzdáno, pozice hráče, čas, vybraná stavba, směr, zpráva…

#### Stavy obrazovky

Proměnná `stav` říká, co je zrovna vidět:

```
          ┌──────── Nastavení ◄──────┐
          │  (Zpět / Esc)            │
          ▼                          │
      ┌──────┐  Hrát 1/3/5 min   ┌──────┐   čas vypršel   ┌───────┐
      │ menu │ ────────────────► │ hra  │ ──────────────► │ konec │
      └──────┘ ◄──────────────── └──────┘                 └───────┘
          │ ▲        Esc                                      │
          │ └───────────────────── Zpět do menu / Enter ──────┘
          ▼
      Ovládání (Zpět / Esc → menu)
```

#### Kostra smyčky ([hra.py:754](hra.py#L754))

```python
while bezi:
    dt = hodiny.tick(FPS) / 1000       # počká na další snímek, dt = uplynulé sekundy
    udalosti = pygame.event.get()      # všechny klávesy/kliky od minulého snímku
    for udalost in udalosti:
        if udalost.type == pygame.QUIT:   # křížek okna
            bezi = False
    okno.fill(POZADI)                  # smaže obrazovku

    if stav == "menu":       ...
    elif stav == "nastaveni": ...
    elif stav == "ovladani":  ...
    elif stav == "hra":       ...
    elif stav == "konec":     ...

    pygame.display.flip()              # ukáže nakreslený snímek
pygame.quit()
```

`hodiny.tick(FPS)` vrací milisekundy od minulého snímku, proto `/ 1000` → sekundy.

#### Stav „menu“ ([hra.py:766](hra.py#L766))
- Klik na „Hrát – 1/3/5“ nastaví `minuty`. Když `minuty > 0`, **všechno se vynuluje**
  (nová mapa, prázdný inventář, hráč doprostřed, čas = minuty · 60) a `stav = "hra"`.
- „Nastavení“ → `stav = "nastaveni"`, „Ovládání“ → `stav = "ovladani"`.
- „Web – výsledky“ → `webbrowser.open(...)` otevře prohlížeč.
- „Konec“ → `bezi = False` → smyčka skončí.
- Kreslí nadpis, tlačítka a dole „Přihlášen: jméno“ nebo „Nepřihlášen – skóre se neuloží“.

#### Stav „nastaveni“ ([hra.py:814](hra.py#L814))
- `−` / `+` mění hlasitost po 10. `max(0, ...)` a `min(100, ...)` hlídají, aby nešla pod 0 a nad 100.
- Přepínače používají trik `volby["fps"] = 1 - volby["fps"]`: z 0 udělá 1 a z 1 udělá 0.
- Barva: `(volby["barva"] + 1) % len(BARVY_HRACE)` – další barva, po poslední zase první
  (`%` = zbytek po dělení).
- Celá obrazovka: změní volbu a znovu otevře okno (`okno = otevri_okno()`).
- **Po každém kliknutí** se volby uloží (`uloz_volby()`) a nastaví hlasitost.
- Texty na přepínačích se každý snímek přepíšou na „ZAP“/„VYP“ podle voleb
  (`"ZAP" if volby["fps"] == 1 else "VYP"` = zkrácený if).

#### Stav „ovladani“ ([hra.py:860](hra.py#L860))
Jen vypíše seznam kláves (seznam dvojic `[klávesa, popis]`) a tipy. Zpět / Esc → zpět.

#### Stav „hra“ ([hra.py:896](hra.py#L896)) – samotné hraní
Probíhá ve třech krocích, jako každá hra:

**1. Vstupy**
- Spočítá, na kterém políčku je **myš** a na kterém **hráč** (podle středu hráče).
- Klávesy (událost `KEYDOWN`):
  - `Esc` – když je vybraná stavba, zruší výběr; jinak zpět do menu (hra se neuloží),
  - `E` – `stiskni_e(...)` a zpráva na 2,5 s,
  - `R` – otočí směr (`(smer + 1) % 4`),
  - `Q` – zruší výběr,
  - `1`–`4` – vybere stavbu (druhý stisk stejné klávesy výběr zruší).
- Myš (událost `MOUSEBUTTONDOWN`):
  - levé tlačítko (1) s vybranou stavbou → `proc_nejde_stavet` → buď `postav`, nebo zpráva s důvodem,
  - pravé tlačítko (3) → `zbourej`.
- **Tažení pásu:** když je vybraný pás a levé tlačítko je **držené**
  (`pygame.mouse.get_pressed()[0]`), staví se pás na každé políčko, přes které myš přejede.
- **Pohyb:** `pygame.key.get_pressed()` řekne, které klávesy jsou právě držené.
  Pozice se mění o `RYCHLOST_HRACE * dt`. `max`/`min` nedovolí hráči utéct z mapy.

> Rozdíl: **událost `KEYDOWN`** přijde jednou při stisku (dobré pro E, R, 1–4),
> **`get_pressed()`** říká, co je drženo právě teď (dobré pro plynulý pohyb).

**2. Logika**
- `aktualizuj_stroje(dt)`, `aktualizuj_pasy(dt)` – továrna jede.
- Odečte čas (`zbyva -= dt`) a čas zprávy.
- **Konec hry** (`zbyva <= 0`): spočítá skóre. Když hráč není přihlášený, nic neukládá;
  jinak zavolá `uloz_do_databaze(...)`. Výsledek uložení si zapamatuje do `ulozeno`
  a přepne `stav = "konec"`.

**3. Kreslení** – v pořadí: mapa → pásy → stroje → náhled stavby → hráč → horní lišta → spodek.

#### Stav „konec“ ([hra.py:989](hra.py#L989))
Ukáže „ČAS VYPRŠEL“, body, co se odeslalo a jestli se výsledek uložil.
„Zpět do menu“ nebo Enter → menu, „Výsledky na webu“ → otevře prohlížeč.

---

## 3. web/app.py – web

Web je napsaný ve **Flasku** (stejně jako ve výuce). Každá stránka = jedna funkce
s `@app.route(...)`. SQL je přímo v kódu.

### Začátek ([app.py:15](web/app.py#L15))

```python
import os, subprocess, sys, bcrypt, mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session
```
- `bcrypt` – hashování hesel, `subprocess` – spuštění hry, `sys` – cesta k Pythonu.

```python
SLOZKA_PROJEKTU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(SLOZKA_PROJEKTU)
from pripojeni import *
```
`app.py` je ve složce `web`, ale `pripojeni.py` (a `hra.py`) jsou o složku výš.
`SLOZKA_PROJEKTU` = složka `Projekt`. `sys.path.append` řekne Pythonu,
ať při `import` hledá i tam.

```python
app = Flask(__name__)
app.secret_key = "astrallift_tajny_klic"
```
Vytvoří webovou aplikaci. `secret_key` je potřeba pro `session` – Flask jím
„podepisuje“ cookie s přihlášením, aby si ji nikdo nemohl změnit.

### `pripoj()` ([app.py:33](web/app.py#L33))
Vrátí připojení k databázi. Je to funkce, ať se nemusí pořád opisovat 4 údaje.

### `vytvor_tabulky()` ([app.py:44](web/app.py#L44))
Spustí se jednou při startu webu. Vytvoří 4 tabulky příkazem `CREATE TABLE IF NOT EXISTS`
(= „vytvoř, jen když ještě neexistuje“) – podrobně v [kapitole 6](#6-databáze).
Potom:
- když je tabulka `ast_predmety` prázdná (`SELECT COUNT(*)` = 0), vloží ruda/ingot/plech,
- když v databázi nejsou žádní hráči, zavolá `vloz_vzorova_data`.
- `commit()` vše potvrdí.

### `vloz_vzorova_data(mycursor)` ([app.py:102](web/app.py#L102))
Vloží 3 vzorové hráče (**Hrac1, Pepa, Lucka**, heslo **heslo123**) a každému jednu hru.
Zadání chce aspoň 3 vzorové záznamy v každé tabulce. Postup je stejný jako
při ukládání hry ve `hra.py` (najdi id hráče → vlož hru → zjisti id hry → vlož předměty).
Seznam `vzorove_hry` obsahuje n-tice `(jméno, minuty, ruda, ingot, plech)`;
cyklus `for jmeno, minuty, ruda, ingot, plech in vzorove_hry:` je rovnou „rozbalí“.

### Stránky (routes)

| Adresa | Funkce | Řádek | Co dělá | Šablona |
|--------|--------|-------|---------|---------|
| `/` | `index` | [134](web/app.py#L134) | úvodní stránka | `index.html` |
| `/autor` | `autor` | [140](web/app.py#L140) | o autorovi | `autor.html` |
| `/vysledky` | `vysledky` | [146](web/app.py#L146) | výsledky z databáze | `vysledky.html` |
| `/prihlaseni` | `prihlaseni` | [200](web/app.py#L200) | přihlášení (GET = formulář, POST = ověření) | `prihlaseni.html` |
| `/registrace` | `registrace` | [231](web/app.py#L231) | registrace (jen POST) | `prihlaseni.html` |
| `/odhlaseni` | `odhlaseni` | [265](web/app.py#L265) | odhlášení | – (přesměruje na `/`) |
| `/hrat` | `hrat` | [276](web/app.py#L276) | spuštění hry (jen POST) | `index.html` |

Každá stránka posílá do šablony `jmeno=session.get("jmeno")` – jméno přihlášeného
hráče, nebo `None`. Podle toho navigace ukáže „Přihlásit“, nebo „Odhlásit“.

### `vysledky()` ([app.py:146](web/app.py#L146))
1. `hledat = request.args.get("hledat", "")` – text z políčka Hledat (z adresy
   `/vysledky?hledat=pepa`); když tam nic není, je to `""`.
2. **Žebříček** – 20 nejlepších her se jménem hráče:
   ```sql
   SELECT ast_hraci.jmeno, ast_hry.skore, ast_hry.delka_minut, ast_hry.datum
   FROM ast_hry
   JOIN ast_hraci ON ast_hraci.id = ast_hry.hrac_id      -- připoj jméno hráče
   WHERE ast_hraci.jmeno LIKE %s                         -- hledání
   ORDER BY ast_hry.skore DESC                           -- od nejlepšího
   LIMIT 20
   ```
   Do `%s` se dosadí `"%" + hledat + "%"`. `%` v LIKE znamená „cokoliv“, takže
   `%ep%` najde „Pepa“. Když se nehledá, je to `%%` = všichni.
3. **Nejlepší hráči** – pro každého hráče nejlepší skóre a počet her:
   ```sql
   SELECT ast_hraci.jmeno, MAX(ast_hry.skore), COUNT(ast_hry.id)
   FROM ast_hraci JOIN ast_hry ON ast_hry.hrac_id = ast_hraci.id
   GROUP BY ast_hraci.jmeno                              -- jeden řádek za hráče
   ORDER BY MAX(ast_hry.skore) DESC
   ```
4. **Moje hry** – jen když je někdo přihlášený (`if "jmeno" in session`),
   jeho hry od nejnovější (`WHERE ast_hraci.jmeno = %s ORDER BY ast_hry.datum DESC`).
5. `fetchall()` vrátí **seznam řádků**, každý řádek je n-tice, např.
   `("Pepa", 120, 3, datum)`. V šabloně se pak čte `hra[0]`, `hra[1]`…
6. Když databáze nejde, `except` uloží chybovou hlášku do `chyba` a stránka ji ukáže.

### `prihlaseni()` ([app.py:200](web/app.py#L200))
- **GET** (jen otevření stránky) → ukáže formuláře.
- **POST** (odeslaný formulář):
  1. vezme `jmeno` a `heslo` z `request.form`,
  2. najde v databázi uložený hash hesla (`SELECT jmeno, heslo FROM ast_hraci WHERE jmeno = %s`),
  3. `bcrypt.checkpw(heslo, hash)` – ověří, jestli zadané heslo patří k uloženému hashi,
     - `.encode("utf-8")` převede text na bajty – bcrypt pracuje s bajty,
     - `except ValueError` – kdyby hash byl v jiném formátu, heslo prostě „nesedí“,
  4. když sedí → `session["jmeno"] = ...` (hráč je přihlášený) a přesměruje na úvod,
  5. jinak ukáže „Špatné jméno nebo heslo“. Neprozrazuje, jestli je špatně jméno, nebo heslo.

### `registrace()` ([app.py:231](web/app.py#L231))
1. Kontrola: jméno 3–30 znaků (`len`), heslo aspoň 6 znaků. `strip()` ořízne mezery.
2. Je jméno volné? (`SELECT id ... WHERE jmeno = %s` – když něco vrátí, je obsazené.)
3. `bcrypt.hashpw(heslo, bcrypt.gensalt())` vyrobí hash. `gensalt()` přidá náhodnou
   „sůl“, takže dvě stejná hesla mají různý hash.
4. `INSERT` + `commit()`.
5. Rovnou přihlásí (`session["jmeno"] = jmeno`) a přesměruje na úvod.

### `odhlaseni()` ([app.py:265](web/app.py#L265))
`session.pop("jmeno", None)` – zapomene přihlášeného hráče.

### `hrat()` ([app.py:276](web/app.py#L276))
1. Nepřihlášeného pošle na přihlášení.
2. Zapíše jméno do `prihlaseny.txt` ve složce Projekt (odtud si ho přečte hra).
3. `subprocess.Popen([sys.executable, ".../hra.py"])` – spustí hru jako **nový program**.
   `sys.executable` = cesta k Pythonu, kterým běží web (aby se hra spustila stejným
   Pythonem se stejnými knihovnami). `Popen` nečeká, až hra skončí – web běží dál.
4. Ukáže úvodní stránku se zprávou „Hra se spouští…“.

### Start webu ([app.py:297](web/app.py#L297))
```python
if __name__ == "__main__":
    vytvor_tabulky()
    app.run(debug=True)
```
`if __name__ == "__main__":` = „jen když se tento soubor spouští přímo“ (`python web/app.py`).
`app.run(debug=True)` spustí web na http://127.0.0.1:5000. `debug=True` znamená, že se web
po uložení změny v kódu **sám restartuje** a při chybě ukáže podrobnou chybovou stránku.

---

## 4. HTML šablony (web/templates)

Šablona = HTML stránka s „dírami“, které doplní Flask:

| Zápis | Význam |
|-------|--------|
| `{{ jmeno }}` | vypiš hodnotu proměnné (Flask ji poslal přes `render_template(..., jmeno=...)`) |
| `{% if jmeno %} … {% else %} … {% endif %}` | podmínka |
| `{% for hra in zebricek %} … {% endfor %}` | cyklus |
| `{{ url_for('static', filename='styly.css') }}` | správná adresa k CSS souboru |

Proto stránky **nejdou otevřít dvojklikem** – bez Flasku by tam zůstaly ty `{{ }}`
a CSS by se nenačetlo. Vždy přes http://127.0.0.1:5000.

**Navigace** (`<nav>`) je na začátku **každé** ze 4 stránek stejná. Když v ní chceš
něco změnit, změň to ve všech čtyřech souborech.

| Šablona | Co obsahuje |
|---------|-------------|
| [index.html](web/templates/index.html) | popis hry; **tlačítko Hrát** – formulář `<form method="POST" action="/hrat">` (jen pro přihlášené, jinak výzva k přihlášení); zpráva „Hra se spouští“; pravidla, tabulka staveb, tabulka ovládání |
| [vysledky.html](web/templates/vysledky.html) | formulář **Hledat** (`method="GET"` → text jde do adresy `?hledat=`); tabulky **Žebříček**, **Nejlepší hráči**, **Moje hry**. `loop.index` = pořadové číslo řádku (1, 2, 3…). `hra[3].strftime("%d. %m. %Y %H:%M")` naformátuje datum na „24. 11. 2026 17:30“ |
| [autor.html](web/templates/autor.html) | jméno autora a použité technologie |
| [prihlaseni.html](web/templates/prihlaseni.html) | dva formuláře vedle sebe: **Přihlášení** (posílá na `/prihlaseni`) a **Registrace** (posílá na `/registrace`); chybové hlášky `chyba` a `chyba_registrace` |

**Propojení formuláře s Pythonem:** atribut `name` u `<input>` je klíč v `request.form`.
`<input name="jmeno">` → v Pythonu `request.form["jmeno"]`.
Atributy `required`, `minlength`, `maxlength` hlídá už prohlížeč (Python to pro jistotu kontroluje znovu).

---

## 5. CSS (web/static/styly.css)

Jeden soubor pro vzhled všech stránek. Pravidlo = **co** (selektor) + **jak** (vlastnosti).

| Pravidlo | Co nastavuje |
|----------|--------------|
| `body` | tmavé pozadí, světlé písmo, písmo Arial |
| `a`, `h1, h2` | fialové odkazy a nadpisy |
| `nav` | lišta nahoře: `display: flex` = položky vedle sebe, `gap` = mezery |
| `nav a`, `nav a:hover` | odkazy v liště; `:hover` = když je nad nimi myš |
| `nav .logo` | tučný větší nápis ASTRALLIFT |
| `nav .ucet` | `margin-left: auto` odsune přihlášení úplně doprava |
| `main` | obsah stránky max. 900 px široký, uprostřed (`margin: 0 auto`) |
| `table`, `th, td`, `th` | tabulky přes celou šířku, čáry mezi řádky, tmavší hlavička |
| `form`, `input` | formuláře pod sebou (`flex-direction: column`), tmavá políčka |
| `button`, `button:hover` | fialová tlačítka |
| `button.hrat` | velké zelené tlačítko Hrát (třída `class="hrat"`) |
| `form.hledani` | hledání: políčko a tlačítko **vedle sebe** (`flex-direction: row`) |
| `.dva-sloupce` | přihlášení a registrace vedle sebe |
| `.chyba`, `.info` | červený a modrý rámeček pro hlášky |

Tečka (`.chyba`) = třída (`class="chyba"`), bez tečky (`nav`) = HTML značka.

---

## 6. Databáze

Všechny tabulky mají předponu **`ast_`**, protože školní databáze `vyuka14` je sdílená
a jsou v ní tabulky ostatních (třeba jiná tabulka `hraci`).

```
ast_hraci (1) ───< (N) ast_hry (1) ───< (N) ast_odevzdane_predmety (N) >─── (1) ast_predmety
```

| Tabulka | Sloupce | K čemu je |
|---------|---------|-----------|
| `ast_hraci` | `id` (PK), `jmeno` (UNIQUE), `heslo` (hash), `registrovan` | účty hráčů |
| `ast_hry` | `id` (PK), `hrac_id` (FK → ast_hraci), `delka_minut`, `skore`, `datum` | odehrané hry |
| `ast_predmety` | `id` (PK), `nazev` (UNIQUE), `body` | ruda, ingot, plech |
| `ast_odevzdane_predmety` | `hra_id` (FK), `predmet_id` (FK), `pocet`; PK je dvojice (`hra_id`, `predmet_id`) | kolik čeho se v které hře odeslalo |

**Vztahy:**
- **1:N** – jeden hráč má mnoho her (`ast_hry.hrac_id` ukazuje na `ast_hraci.id`).
- **M:N** – jedna hra obsahuje víc druhů předmětů a jeden předmět je v mnoha hrách.
  Proto je mezi nimi **vazební tabulka** `ast_odevzdane_predmety`.

**Vlastnosti sloupců:**
- `INT`, `VARCHAR(30)`, `DATETIME` – datové typy (číslo, text do 30 znaků, datum a čas),
- `NOT NULL` – musí být vyplněno, `UNIQUE` – nesmí se opakovat (dvě stejná jména),
- `DEFAULT CURRENT_TIMESTAMP` – když se nezadá, doplní se aktuální čas,
- `ON DELETE CASCADE` – když se smaže hráč, smažou se automaticky i jeho hry.

**Kde je jaké SQL:**

| SQL | Kde |
|-----|-----|
| `CREATE TABLE` | `vytvor_tabulky()` v [web/app.py](web/app.py#L44) |
| `INSERT` vzorová data | `vloz_vzorova_data()` v [web/app.py](web/app.py#L102) |
| `INSERT` registrace | `registrace()` v [web/app.py](web/app.py#L231) |
| `INSERT` výsledek hry | `uloz_do_databaze()` v [hra.py](hra.py#L159) |
| `SELECT` s JOIN, WHERE, LIKE, ORDER BY, LIMIT | `vysledky()` – žebříček |
| `SELECT` s GROUP BY, MAX, COUNT | `vysledky()` – nejlepší hráči |
| `SELECT` přihlášení | `prihlaseni()` |

---

## 7. Ostatní soubory

| Soubor | Co to je |
|--------|----------|
| `pripojeni.py` | 4 proměnné: `HOST`, `USER`, `PASSWORD`, `DATABASE`. Je v `.gitignore` → **nejde na GitHub** (je v něm heslo) |
| `requirements.txt` | knihovny pro `pip install -r requirements.txt`: pygame, mysql-connector-python, flask, bcrypt. Moduly `os`, `sys`, `subprocess`, `webbrowser` jsou součástí Pythonu, proto jsou tam jen v komentáři |
| `hudba.wav` | hudba ve hře (vygenerovaná programem, žádná cizí hudba) |
| `volby.txt` | vytváří ho hra – uložené nastavení (`hudba=50` …). Jde smazat, hra začne s výchozím |
| `prihlaseny.txt` | vytváří ho web – jméno hráče pro hru. Hra ho po přečtení vymaže |
| `.gitignore` | seznam souborů, které se nemají posílat na GitHub |
| `README.md` | stručný popis projektu, spuštění, ER diagram |
| `README_hra.md` | návod krok za krokem, jak to spustit ve VS Code |

### Co jsme v hodinách nebrali (a proč to tam je)

| Věc | Kde | Proč |
|-----|-----|------|
| `subprocess.Popen` | `web/app.py` | bez toho nejde z webu spustit hru (tlačítko Hrát) |
| `sys.executable`, `sys.path.append` | `web/app.py` | aby web spustil hru stejným Pythonem a našel `pripojeni.py` o složku výš |
| `webbrowser.open` | `hra.py` | tlačítko „Web – výsledky“ ve hře otevře prohlížeč |
| `os.chdir`, `os.path` | `hra.py`, `web/app.py` | aby se našly soubory, ať program spustíš odkudkoli |

---

## 8. Jak udělat typické změny

### Zrychlit nebo zpomalit hráče
[hra.py:47](hra.py#L47): `RYCHLOST_HRACE = 250` → třeba `400`.

### Změnit cenu nebo rychlost stroje
[hra.py:72](hra.py#L72), slovník `STROJE`. Např. levnější pec: u `"pec"` změň `"cena": 10` na `"cena": 6`.
Rychlejší lis: `"doba": 3` → `"doba": 1`.
Pozor: ceny jsou napsané i v textech (ovládání ve hře, `index.html`) – ty se samy nezmění.

### Změnit body za předmět
[hra.py:64](hra.py#L64): `BODY = {"ruda": 1, "ingot": 2, "plech": 4}`. Skóre počítá hra právě odtud.
(V databázi je sloupec `ast_predmety.body` jen informační. Kdybys ho chtěl taky změnit:
`UPDATE ast_predmety SET body = 3 WHERE nazev = 'ingot'`.)

### Přidat délku hry 10 minut
1. U ostatních tlačítek v menu ([hra.py:710](hra.py#L710)) přidej:
   `tl_hrat_10 = Tlacitko("Hrát – 10 minut", SIRKA // 2, 415)` (a posuň tlačítka pod ním níž).
2. V menu ([hra.py:770](hra.py#L770)) přidej:
   ```python
   if tl_hrat_10.kliknuto(udalost):
       minuty = 10
   ```
3. Přidej `tl_hrat_10` do seznamu tlačítek, která se kreslí ([hra.py:803](hra.py#L803)).

### Přesunout rudu nebo výtah
[hra.py:52](hra.py#L52) – `RUDA_X`, `RUDA_Y`, … a [hra.py:58](hra.py#L58) – `VYTAH_X`, …
(v políčkách: sloupce 0–31, řádky 0–15).

### Změnit text nebo barvu na webu
- Text: v `web/templates/*.html` (obyčejné HTML).
- Barvy: `web/static/styly.css`, např. barva tlačítek je `background: #6a5acd;` u `button`.
- Web se díky `debug=True` sám přenačte, v prohlížeči stačí F5.

### Přidat novou stránku na web
1. Vytvoř `web/templates/novinky.html` (zkopíruj třeba `autor.html` a změň obsah v `<main>`).
2. Do `web/app.py` přidej:
   ```python
   @app.route("/novinky")
   def novinky():
       """Stránka s novinkami."""
       return render_template("novinky.html", jmeno=session.get("jmeno"))
   ```
3. Do navigace (`<nav>`) ve **všech** šablonách přidej `<a href="/novinky">Novinky</a>`.

### Přidat sloupec do žebříčku
Např. ID hry: v `vysledky()` přidej do SELECTu `ast_hry.id` (bude to `hra[4]`)
a ve `vysledky.html` přidej `<th>ID</th>` a `<td>{{ hra[4] }}</td>`.

---

## 9. Otázky, které můžou padnout u maturity

**Jak funguje herní smyčka?**
Je to `while` cyklus, který běží 60× za sekundu. Každý průchod: 1) přečte vstupy
(klávesy, myš), 2) aktualizuje logiku (pohyb, stroje, pásy, čas), 3) všechno nakreslí
a `flip()` to ukáže.

**Co je `dt` a proč ho používáš?**
Čas od minulého snímku v sekundách. Pohyb `rychlost * dt` je pak stejně rychlý
na rychlém i pomalém počítači.

**Jak máš uloženou mapu?**
2D seznam `mapa[radek][sloupec]`. Na políčku je `None`, nebo slovník s pásem či strojem.
Stroj 2×1 má na obou políčkách ten samý slovník.

**Jak se pozná, co je na políčku pod myší?**
`sloupec = x // 40`, `radek = (y − 80) // 40` (80 je výška horní lišty).

**Jak funguje pás?**
Každý pás nese max. 1 věc a `posun` od 0 do 1. Každý snímek se posun zvětší
o `RYCHLOST_PASU * dt`. Na konci (1) se věc předá funkcí `vloz_predmet` dál –
na další pás, do stroje nebo do výtahu.

**Jak se počítají body?**
Funkce `spocitej_body` vynásobí počet odeslaných kusů body za kus (`BODY`) a sečte je.

**Jak se ukládá nastavení?**
Do textového souboru `volby.txt`, řádek `klic=hodnota`. Načítá se přes `split("=")`.

**Proč se heslo ukládá jako hash?**
Kdyby někdo ukradl databázi, hesla nezjistí. Hash (bcrypt) nejde převést zpátky na heslo.
Při přihlášení `bcrypt.checkpw` porovná zadané heslo s uloženým hashem.

**Co je SQL injection a jak se bráníš?**
Útok, kdy někdo napíše do formuláře kus SQL příkazu. Bráním se tím, že hodnoty
nevkládám do textu dotazu, ale přes `%s` – knihovna je vloží bezpečně.

**Co je session?**
Paměť webu pro přihlášeného uživatele. Po přihlášení `session["jmeno"] = ...`,
po odhlášení `session.pop("jmeno")`. Uložená je v cookie, podepsané `secret_key`.

**Jak se dostane jméno hráče z webu do hry?**
Web ho zapíše do souboru `prihlaseny.txt` a spustí `hra.py`. Hra soubor přečte
a vymaže.

**Co je u tebe 1:N a M:N?**
1:N – jeden hráč, mnoho her (`ast_hry.hrac_id`). M:N – hry a předměty přes vazební
tabulku `ast_odevzdane_predmety`.

**Co dělá JOIN v žebříčku?**
V tabulce her je jen `hrac_id`. JOIN připojí tabulku hráčů, abych mohl vypsat jméno.

**K čemu je GROUP BY?**
Seskupí hry podle hráče, takže pro každého hráče spočítám `MAX(skore)` a `COUNT(id)`.

**Proč mají tabulky předponu `ast_`?**
Školní databáze je sdílená a jsou v ní tabulky jiných lidí se stejnými názvy.

**Co se stane, když nejde databáze?**
Hra i web jsou v `try / except`. Hra dohraje a napíše, že se výsledek neuložil,
web ukáže hlášku „Databáze není dostupná“. Nic nespadne.

**Jak funguje tlačítko v menu?**
Třída `Tlacitko` má obdélník (`Rect`). Při kliknutí se zkontroluje, jestli je bod
kliknutí uvnitř obdélníku (`collidepoint`).

**Jak přepínáš obrazovky (menu, hra…)?**
Proměnná `stav` (`"menu"`, `"nastaveni"`, `"ovladani"`, `"hra"`, `"konec"`).
V hlavní smyčce `if stav == ...` rozhodne, co se kreslí a jak se reaguje na vstupy.
