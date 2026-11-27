# =====================================================================
#  ASTRALLIFT – HRA
#
#  Spuštění:  python hra.py
#  (nebo z webu tlačítkem "Hrát" – pak se skóre uloží do databáze)
#
#  Celá hra je v tomhle jednom souboru. Je rozdělená na části:
#    1) NASTAVENÍ HRY     – čísla, která můžeš měnit (rychlost, ceny...)
#    2) VOLBY HRÁČE       – hlasitost atd., ukládají se do souboru volby.txt
#    3) DATABÁZE          – uložení skóre (SQL přímo tady)
#    4) HUDBA
#    5) TLAČÍTKO          – třída pro tlačítka v menu
#    6) MAPA A STAVĚNÍ    – herní logika (těžba, stroje, pásy, výtah)
#    7) KRESLENÍ
#    8) HLAVNÍ SMYČKA     – menu, nastavení, ovládání, hra, konec hry
# =====================================================================

import os
import webbrowser
import pygame
import mysql.connector

# Přihlašovací údaje k databázi (HOST, USER, PASSWORD, DATABASE).
# Když soubor pripojeni.py chybí, hra pojede dál, jen se neuloží skóre.
try:
    from pripojeni import *
except ImportError:
    print("Chybí soubor pripojeni.py – skóre se nebude ukládat.")

# Přepneme se do složky, kde leží tento soubor.
# Díky tomu najdeme hudbu a soubory .txt, ať hru spustíme odkudkoli.
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# =====================================================================
#  1) NASTAVENÍ HRY – tady se dají měnit čísla
# =====================================================================

SIRKA = 1280                 # šířka okna v pixelech
VYSKA = 720                  # výška okna v pixelech
FPS = 60                     # kolikrát za sekundu se hra překreslí
DLAZDICE = 40                # mapa je ze čtverečků 40 × 40 pixelů
LISTA = 80                   # výška horního pruhu (čas, body, inventář)
SLOUPCU = SIRKA // DLAZDICE  # 32 sloupců
RADKU = (VYSKA - LISTA) // DLAZDICE  # 16 řádků

RYCHLOST_HRACE = 250         # pixelů za sekundu
VELIKOST_HRACE = 28          # hráč je čtverec 28 × 28 pixelů
ADRESA_WEBU = "http://127.0.0.1:5000"

# Ložisko rudy (vlevo): od kterého sloupce/řádku a jak je velké (v dlaždicích)
RUDA_X = 1
RUDA_Y = 4
RUDA_SIRKA = 5
RUDA_VYSKA = 8

# Vesmírný výtah (vpravo)
VYTAH_X = 27
VYTAH_Y = 6
VYTAH_SIRKA = 3
VYTAH_VYSKA = 4

# Kolik bodů je za jeden kus předmětu
BODY = {"ruda": 1, "ingot": 3, "plech": 8}

# Stroje:
#   cena     = kolik rudy stojí postavení
#   vstup    = co stroj spotřebuje (None = nic, těžič bere rudu ze země)
#   vystup   = co stroj vyrobí
#   doba     = za kolik sekund vyrobí 1 kus
#   velikost = 1 (stroj 1×1) nebo 2 (stroj 2×1 – vstupní a výstupní polovina)
STROJE = {
    "tezic": {"nazev": "Těžič", "cena": 5, "vstup": None, "vystup": "ruda",
              "doba": 2, "velikost": 1, "barva": (210, 150, 40)},
    "pec": {"nazev": "Pec", "cena": 10, "vstup": "ruda", "vystup": "ingot",
            "doba": 2, "velikost": 2, "barva": (190, 75, 55)},
    "lis": {"nazev": "Lis", "cena": 15, "vstup": "ingot", "vystup": "plech",
            "doba": 3, "velikost": 2, "barva": (70, 140, 200)},
}
MAX_ZASOBA = 20              # kolik se max. vejde do stroje (na vstup i na výstup)

CENA_PASU = 1                # pás stojí 1 rudu za políčko
RYCHLOST_PASU = 2            # kolik políček za sekundu ujede věc na pásu

# Klávesa -> co se bude stavět
KLAVESY_STAVEB = {pygame.K_1: "tezic", pygame.K_2: "pec", pygame.K_3: "lis", pygame.K_4: "pas"}
STAVBY = ["tezic", "pec", "lis", "pas"]     # pořadí v liště nahoře

# Směry: [posun ve sloupcích, posun v řádcích]. Číslo směru = pozice v seznamu.
SMERY = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # 0 = vpravo, 1 = dolů, 2 = vlevo, 3 = nahoru
SIPKY = ["→", "↓", "←", "↑"]

# Barvy, které si hráč může vybrat v Nastavení
NAZVY_BAREV = ["Žlutá", "Modrá", "Zelená", "Růžová", "Oranžová"]
BARVY_HRACE = [(240, 240, 90), (90, 170, 255), (110, 230, 120), (255, 130, 200), (255, 160, 60)]

# Další barvy (R, G, B)
BILA = (235, 235, 235)
SEDA = (150, 150, 170)
CERNA = (20, 20, 20)
ZLUTA = (255, 220, 120)
CERVENA = (255, 90, 90)
ZELENA = (120, 220, 120)
FIALOVA = (180, 160, 255)
POZADI = (25, 25, 35)


# =====================================================================
#  2) VOLBY HRÁČE – ukládají se do textového souboru volby.txt
#     Každý řádek vypadá takhle:  hudba=50
# =====================================================================

# Výchozí volby (1 = zapnuto, 0 = vypnuto, barva = pořadí v seznamu barev)
volby = {"hudba": 50, "fps": 0, "mrizka": 1, "napoveda": 1, "cela": 0, "barva": 0}


def nacti_volby():
    """Načte volby ze souboru volby.txt (když soubor není, zůstanou výchozí)."""
    try:
        with open("volby.txt", "r", encoding="utf-8") as soubor:
            for radek in soubor:
                casti = radek.strip().split("=")        # "hudba=50" -> ["hudba", "50"]
                if len(casti) == 2 and casti[0] in volby:
                    volby[casti[0]] = int(casti[1])
    except (FileNotFoundError, ValueError):
        print("Volby se nenačetly, používám výchozí.")
    if volby["barva"] >= len(BARVY_HRACE):              # kdyby v souboru bylo nesmyslné číslo
        volby["barva"] = 0


def uloz_volby():
    """Uloží volby do souboru volby.txt."""
    with open("volby.txt", "w", encoding="utf-8") as soubor:
        for klic, hodnota in volby.items():
            soubor.write(f"{klic}={hodnota}\n")


def zjisti_prihlaseneho_hrace():
    """
    Web před spuštěním hry zapíše jméno přihlášeného hráče do souboru prihlaseny.txt.
    Tady ho přečteme a soubor vymažeme (aby se příští hra spuštěná napřímo neuložila pod cizím jménem).
    Vrátí jméno, nebo "" když nikdo není přihlášený.
    """
    jmeno = ""
    try:
        with open("prihlaseny.txt", "r", encoding="utf-8") as soubor:
            jmeno = soubor.read().strip()
    except FileNotFoundError:
        jmeno = ""
    with open("prihlaseny.txt", "w", encoding="utf-8") as soubor:
        soubor.write("")
    return jmeno


# =====================================================================
#  3) DATABÁZE – uložení výsledku hry
# =====================================================================

def uloz_do_databaze(jmeno, minuty, skore, odevzdano):
    """
    Uloží odehranou hru do databáze. Vrátí True (povedlo se) nebo False (chyba).
    odevzdano = kolik čeho hráč poslal výtahem, např. {"ruda": 10, "ingot": 3, "plech": 0}
    """
    try:
        mydb = mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)
        mycursor = mydb.cursor()

        # 1) Najdeme id hráče podle jména
        mycursor.execute("SELECT id FROM ast_hraci WHERE jmeno = %s", (jmeno,))
        hrac_id = mycursor.fetchone()[0]

        # 2) Uložíme hru
        mycursor.execute("INSERT INTO ast_hry (hrac_id, delka_minut, skore) VALUES (%s, %s, %s)",
                         (hrac_id, minuty, skore))

        # 3) Zjistíme id právě uložené hry (je to nejvyšší id her tohoto hráče)
        mycursor.execute("SELECT MAX(id) FROM ast_hry WHERE hrac_id = %s", (hrac_id,))
        hra_id = mycursor.fetchone()[0]

        # 4) Uložíme, co hráč odeslal (jen předměty, kterých bylo víc než 0)
        for nazev, pocet in odevzdano.items():
            if pocet > 0:
                mycursor.execute("SELECT id FROM ast_predmety WHERE nazev = %s", (nazev,))
                predmet_id = mycursor.fetchone()[0]
                mycursor.execute("INSERT INTO ast_odevzdane_predmety (hra_id, predmet_id, pocet) "
                                 "VALUES (%s, %s, %s)", (hra_id, predmet_id, pocet))

        mydb.commit()       # potvrdí všechny změny
        mydb.close()
        return True
    except Exception as chyba:
        print("Chyba databáze:", chyba)
        return False


# =====================================================================
#  4) HUDBA – když počítač nemá zvukovou kartu, hra pojede potichu
# =====================================================================

pygame.init()
hudba_funguje = True
try:
    pygame.mixer.init()
    pygame.mixer.music.load("hudba.wav")
except pygame.error:
    print("Zvuk nefunguje, hra pojede potichu.")
    hudba_funguje = False


def nastav_hlasitost():
    """Nastaví hlasitost hudby podle voleb (0–100 %)."""
    if hudba_funguje:
        pygame.mixer.music.set_volume(volby["hudba"] / 100)


# =====================================================================
#  5) TLAČÍTKO
# =====================================================================

class Tlacitko:
    """Obdélník s textem, na který se dá kliknout myší."""

    def __init__(self, text, x, y, sirka=360, vyska=50):
        self.text = text
        self.rect = pygame.Rect(0, 0, sirka, vyska)
        self.rect.center = (x, y)          # x, y = prostředek tlačítka

    def nakresli(self):
        # Když je nad tlačítkem myš, je světlejší
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            barva = (90, 90, 140)
        else:
            barva = (55, 55, 85)
        pygame.draw.rect(okno, barva, self.rect, border_radius=10)
        pygame.draw.rect(okno, (200, 200, 230), self.rect, 2, border_radius=10)
        napis(self.text, font_stredni, BILA, self.rect.center)

    def kliknuto(self, udalost):
        """Vrátí True, když na tlačítko někdo klikl levým tlačítkem myši."""
        if udalost.type == pygame.MOUSEBUTTONDOWN and udalost.button == 1:
            if self.rect.collidepoint(udalost.pos):
                return True
        return False


# =====================================================================
#  6) MAPA A STAVĚNÍ – herní logika
#
#  Mapa je 2D seznam: mapa[radek][sloupec]
#  Na každém políčku je None (nic) nebo slovník se stavbou:
#    pás:   {"druh": "pas", "smer": 0, "predmet": "ruda" nebo None, "posun": 0 až 1}
#    stroj: {"druh": "pec", "x": ..., "y": ..., "smer": ..., "vstup": počet,
#            "hotovo": počet, "cas": jak dlouho už vyrábí, "pracuje": True/False}
#  Stroj 2×1 je na dvou políčkách – na obou je ten samý slovník.
# =====================================================================

def je_ruda(x, y):
    """Je na políčku (x, y) ruda?"""
    return RUDA_X <= x < RUDA_X + RUDA_SIRKA and RUDA_Y <= y < RUDA_Y + RUDA_VYSKA


def je_vytah(x, y):
    """Je na políčku (x, y) výtah?"""
    return VYTAH_X <= x < VYTAH_X + VYTAH_SIRKA and VYTAH_Y <= y < VYTAH_Y + VYTAH_VYSKA


def je_na_mape(x, y):
    """Leží políčko (x, y) uvnitř mapy?"""
    return 0 <= x < SLOUPCU and 0 <= y < RADKU


def nova_mapa():
    """Vytvoří prázdnou mapu (všude None)."""
    prazdna = []
    for y in range(RADKU):
        prazdna.append([None] * SLOUPCU)
    return prazdna


def spocitej_body(predmety):
    """Sečte body za předměty, např. {"ruda": 3, "ingot": 1, "plech": 0} -> 5."""
    soucet = 0
    for nazev, pocet in predmety.items():
        soucet += pocet * BODY[nazev]
    return soucet


def policka_stavby(druh, x, y, smer_stavby):
    """Vrátí seznam políček, která stavba zabere. U stroje 2×1: [vstupní, výstupní]."""
    if druh != "pas" and STROJE[druh]["velikost"] == 2:
        dx, dy = SMERY[smer_stavby]
        return [(x, y), (x + dx, y + dy)]
    return [(x, y)]


def proc_nejde_stavet(druh, x, y):
    """Vrátí důvod, proč se tady stavět nedá. Když se stavět dá, vrátí "" (prázdný text)."""
    for px, py in policka_stavby(druh, x, y, smer):
        if not je_na_mape(px, py):
            return "Sem se to nevejde."
        if je_vytah(px, py):
            return "Na výtah se stavět nedá."
        if mapa[py][px] is not None:
            return "Tady už něco stojí."
    if druh == "tezic" and not je_ruda(x, y):
        return "Těžič musí stát na rudě."
    if druh == "pas":
        cena = CENA_PASU
    else:
        cena = STROJE[druh]["cena"]
    if inventar["ruda"] < cena:
        return f"Nemáš dost rudy (potřebuješ {cena}, máš {inventar['ruda']})."
    return ""


def postav(druh, x, y):
    """Postaví stavbu na políčko (x, y). Předtím je potřeba zkontrolovat proc_nejde_stavet()."""
    if druh == "pas":
        inventar["ruda"] -= CENA_PASU
        mapa[y][x] = {"druh": "pas", "smer": smer, "predmet": None, "posun": 0}
        return
    inventar["ruda"] -= STROJE[druh]["cena"]
    stroj = {"druh": druh, "x": x, "y": y, "smer": smer,
             "vstup": 0, "hotovo": 0, "cas": 0, "pracuje": False}
    stroje.append(stroj)
    for px, py in policka_stavby(druh, x, y, smer):
        mapa[py][px] = stroj


def zbourej(x, y):
    """Zbourá stavbu na políčku (x, y). Hráč dostane zpět rudu i to, co bylo uvnitř."""
    if not je_na_mape(x, y) or mapa[y][x] is None:
        return "Tady není co bourat."
    vec = mapa[y][x]

    if vec["druh"] == "pas":
        inventar["ruda"] += CENA_PASU
        if vec["predmet"] is not None:
            inventar[vec["predmet"]] += 1
        mapa[y][x] = None
        return "Pás zbourán."

    # Je to stroj
    info = STROJE[vec["druh"]]
    inventar["ruda"] += info["cena"]
    inventar[info["vystup"]] += vec["hotovo"]
    if info["vstup"] is not None:
        inventar[info["vstup"]] += vec["vstup"]
    for px, py in policka_stavby(vec["druh"], vec["x"], vec["y"], vec["smer"]):
        mapa[py][px] = None
    stroje.remove(vec)
    return f"Zbouráno: {info['nazev']} (vráceno {info['cena']} rudy)"


def vloz_predmet(x, y, predmet):
    """
    Zkusí dát 1 předmět na políčko (x, y). Vrátí True, když ho tam něco vzalo:
      - výtah ho odešle (připočítají se body)
      - prázdný pás ho veze dál
      - stroj ho vezme, když ho potřebuje a má místo
    """
    if je_vytah(x, y):
        odevzdano[predmet] += 1
        return True
    if not je_na_mape(x, y) or mapa[y][x] is None:
        return False

    vec = mapa[y][x]
    if vec["druh"] == "pas":
        if vec["predmet"] is None:
            vec["predmet"] = predmet
            vec["posun"] = 0
            return True
        return False

    # Je to stroj
    if STROJE[vec["druh"]]["vstup"] == predmet and vec["vstup"] < MAX_ZASOBA:
        vec["vstup"] += 1
        return True
    return False


def aktualizuj_stroje(dt):
    """Stroje vyrábějí a hotové výrobky posílají na políčko, kam míří jejich šipka."""
    for stroj in stroje:
        info = STROJE[stroj["druh"]]

        # Výroba: stroj potřebuje suroviny (těžič ne) a místo pro výrobky
        ma_suroviny = info["vstup"] is None or stroj["vstup"] > 0
        stroj["pracuje"] = ma_suroviny and stroj["hotovo"] < MAX_ZASOBA
        if stroj["pracuje"]:
            stroj["cas"] += dt
            if stroj["cas"] >= info["doba"]:
                stroj["cas"] = 0
                if info["vstup"] is not None:
                    stroj["vstup"] -= 1
                stroj["hotovo"] += 1

        # Odeslání výrobku na políčko za výstupní stranou stroje
        if stroj["hotovo"] > 0:
            posledni_x, posledni_y = policka_stavby(stroj["druh"], stroj["x"], stroj["y"], stroj["smer"])[-1]
            dx, dy = SMERY[stroj["smer"]]
            if vloz_predmet(posledni_x + dx, posledni_y + dy, info["vystup"]):
                stroj["hotovo"] -= 1


def aktualizuj_pasy(dt):
    """Věci na pásech jedou dopředu. Na konci políčka se předají dál (když je kam)."""
    for y in range(RADKU):
        for x in range(SLOUPCU):
            pas = mapa[y][x]
            if pas is None or pas["druh"] != "pas" or pas["predmet"] is None:
                continue
            pas["posun"] += RYCHLOST_PASU * dt
            if pas["posun"] >= 1:
                pas["posun"] = 1                    # věc čeká na konci pásu
                dx, dy = SMERY[pas["smer"]]
                if vloz_predmet(x + dx, y + dy, pas["predmet"]):
                    pas["predmet"] = None
                    pas["posun"] = 0


def stiskni_e(x, y):
    """Co se stane po stisku E na políčku, kde hráč stojí. Vrátí zprávu pro hráče."""
    # Výtah: odešle vše, co hráč nese
    if je_vytah(x, y):
        body = spocitej_body(inventar)
        if body == 0:
            return "Nemáš nic, co by se dalo odeslat."
        for nazev in inventar:
            odevzdano[nazev] += inventar[nazev]
            inventar[nazev] = 0
        return f"Odesláno výtahem: +{body} bodů"

    vec = mapa[y][x]

    # Pás: sebere věc z pásu
    if vec is not None and vec["druh"] == "pas":
        if vec["predmet"] is None:
            return "Pás je prázdný."
        inventar[vec["predmet"]] += 1
        zprava = f"Sebráno z pásu: {vec['predmet']}"
        vec["predmet"] = None
        return zprava

    # Stroj: vezme hotové výrobky a vloží suroviny
    if vec is not None:
        info = STROJE[vec["druh"]]
        vzato = vec["hotovo"]
        inventar[info["vystup"]] += vzato
        vec["hotovo"] = 0
        zprava = f"{info['nazev']}: vzato {vzato}× {info['vystup']}"
        if info["vstup"] is not None:
            vlozeno = min(inventar[info["vstup"]], MAX_ZASOBA - vec["vstup"])
            vec["vstup"] += vlozeno
            inventar[info["vstup"]] -= vlozeno
            zprava += f", vloženo {vlozeno}× {info['vstup']}"
        return zprava

    # Ruda: vytěží 1 kus
    if je_ruda(x, y):
        inventar["ruda"] += 1
        return "+1 ruda"

    return "Tady nic není. Těž na rudě (hnědá), odesílej ve výtahu (fialový)."


# =====================================================================
#  7) KRESLENÍ
# =====================================================================

def napis(text, font, barva, stred):
    """Napíše text tak, aby jeho prostředek byl v bodě stred."""
    obrazek = font.render(text, True, barva)
    okno.blit(obrazek, obrazek.get_rect(center=stred))


def stred_policka(x, y):
    """Vrátí prostředek políčka (x, y) v pixelech."""
    return x * DLAZDICE + DLAZDICE // 2, LISTA + y * DLAZDICE + DLAZDICE // 2


def nakresli_predmet(nazev, x, y):
    """Nakreslí malou ikonku předmětu se středem v bodě (x, y)."""
    if nazev == "ruda":
        pygame.draw.circle(okno, (150, 95, 55), (x, y), 7)
        pygame.draw.circle(okno, (225, 150, 70), (x - 2, y - 2), 3)
    elif nazev == "ingot":
        pygame.draw.rect(okno, (180, 185, 195), (x - 8, y - 4, 16, 9), border_radius=2)
        pygame.draw.rect(okno, (90, 95, 105), (x - 8, y - 4, 16, 9), 1, border_radius=2)
    elif nazev == "plech":
        pygame.draw.rect(okno, (210, 220, 230), (x - 8, y - 7, 16, 14))
        pygame.draw.rect(okno, (110, 120, 135), (x - 8, y - 7, 16, 14), 1)


def nakresli_sipku(x, y, smer_sipky, barva):
    """Nakreslí malou trojúhelníkovou šipku se středem v (x, y) mířící ve směru smer_sipky."""
    dx, dy = SMERY[smer_sipky]
    kolmo_x, kolmo_y = -dy, dx              # směr otočený o 90°
    spicka = (x + dx * 7, y + dy * 7)
    roh1 = (x - dx * 4 + kolmo_x * 6, y - dy * 4 + kolmo_y * 6)
    roh2 = (x - dx * 4 - kolmo_x * 6, y - dy * 4 - kolmo_y * 6)
    pygame.draw.polygon(okno, barva, [spicka, roh1, roh2])


def nakresli_mapu():
    """Nakreslí zem, rudu a výtah."""
    for y in range(RADKU):
        for x in range(SLOUPCU):
            obdelnik = pygame.Rect(x * DLAZDICE, LISTA + y * DLAZDICE, DLAZDICE, DLAZDICE)
            if je_ruda(x, y):
                pygame.draw.rect(okno, (95, 70, 55), obdelnik)
                pygame.draw.circle(okno, (200, 135, 70), (obdelnik.x + 12, obdelnik.y + 14), 4)  # kousky rudy
                pygame.draw.circle(okno, (165, 110, 60), (obdelnik.x + 27, obdelnik.y + 26), 3)
            elif je_vytah(x, y):
                pygame.draw.rect(okno, (110, 105, 150), obdelnik)
            else:
                pygame.draw.rect(okno, (58, 68, 58), obdelnik)
            if volby["mrizka"] == 1:
                pygame.draw.rect(okno, (48, 56, 48), obdelnik, 1)

    # Výtah: žlutý okraj, světelný paprsek nahoru a blikající světlo
    vytah = pygame.Rect(VYTAH_X * DLAZDICE, LISTA + VYTAH_Y * DLAZDICE,
                        VYTAH_SIRKA * DLAZDICE, VYTAH_VYSKA * DLAZDICE)
    pygame.draw.rect(okno, (230, 190, 40), vytah, 4)
    pygame.draw.line(okno, (200, 190, 255), (vytah.centerx, LISTA), (vytah.centerx, vytah.top - 28), 3)
    if pygame.time.get_ticks() // 500 % 2 == 0:          # každou půlsekundu se přepne
        pygame.draw.circle(okno, CERVENA, (vytah.left + 8, vytah.top + 8), 4)

    # Popisky
    napis("VÝTAH", font_maly, BILA, (vytah.centerx, vytah.top - 14))
    napis("RUDA", font_maly, BILA, ((RUDA_X + RUDA_SIRKA / 2) * DLAZDICE, LISTA + RUDA_Y * DLAZDICE - 14))


def nakresli_pasy():
    """Nakreslí všechny pásy a věci, které po nich jedou."""
    for y in range(RADKU):
        for x in range(SLOUPCU):
            pas = mapa[y][x]
            if pas is None or pas["druh"] != "pas":
                continue
            stred_x, stred_y = stred_policka(x, y)
            pygame.draw.rect(okno, (45, 45, 52), (x * DLAZDICE + 2, LISTA + y * DLAZDICE + 2, 36, 36), border_radius=4)
            nakresli_sipku(stred_x, stred_y, pas["smer"], (95, 95, 110))
            if pas["predmet"] is not None:
                # Věc se posouvá od začátku políčka (posun 0) ke konci (posun 1)
                dx, dy = SMERY[pas["smer"]]
                vec_x = stred_x + int(dx * (pas["posun"] - 0.5) * DLAZDICE)
                vec_y = stred_y + int(dy * (pas["posun"] - 0.5) * DLAZDICE)
                nakresli_predmet(pas["predmet"], vec_x, vec_y)


def nakresli_stroje():
    """Nakreslí stroje. Pec a lis ukazují vstup (suroviny) a výstup (výrobky)."""
    for stroj in stroje:
        info = STROJE[stroj["druh"]]
        policka = policka_stavby(stroj["druh"], stroj["x"], stroj["y"], stroj["smer"])
        x1, y1 = policka[0]          # první (vstupní) políčko
        x2, y2 = policka[-1]         # poslední (výstupní) políčko

        # Obdélník přes obě políčka
        levy = min(x1, x2) * DLAZDICE + 2
        horni = LISTA + min(y1, y2) * DLAZDICE + 2
        sirka = (abs(x2 - x1) + 1) * DLAZDICE - 4
        vyska = (abs(y2 - y1) + 1) * DLAZDICE - 4
        obdelnik = pygame.Rect(levy, horni, sirka, vyska)
        pygame.draw.rect(okno, info["barva"], obdelnik, border_radius=6)
        pygame.draw.rect(okno, CERNA, obdelnik, 2, border_radius=6)

        if info["velikost"] == 1:
            # Těžič: vrták. Když pracuje, střídají se dva tvary -> vypadá to, že se točí.
            stred_x, stred_y = stred_policka(x1, y1)
            pygame.draw.circle(okno, (80, 80, 90), (stred_x, stred_y), 12)
            if stroj["pracuje"] and pygame.time.get_ticks() // 150 % 2 == 0:
                pygame.draw.line(okno, BILA, (stred_x - 8, stred_y - 8), (stred_x + 8, stred_y + 8), 3)
                pygame.draw.line(okno, BILA, (stred_x - 8, stred_y + 8), (stred_x + 8, stred_y - 8), 3)
            else:
                pygame.draw.line(okno, BILA, (stred_x - 10, stred_y), (stred_x + 10, stred_y), 3)
                pygame.draw.line(okno, BILA, (stred_x, stred_y - 10), (stred_x, stred_y + 10), 3)
            napis(str(stroj["hotovo"]), font_maly, CERNA, (stred_x + 12, stred_y + 13))
        else:
            # Pec / lis: na vstupní polovině surovina a její počet, na výstupní výrobek a jeho počet
            stred_x, stred_y = stred_policka(x1, y1)
            nakresli_predmet(info["vstup"], stred_x, stred_y - 6)
            napis(str(stroj["vstup"]), font_maly, CERNA, (stred_x, stred_y + 11))
            stred_x, stred_y = stred_policka(x2, y2)
            nakresli_predmet(info["vystup"], stred_x, stred_y - 6)
            napis(str(stroj["hotovo"]), font_maly, CERNA, (stred_x, stred_y + 11))

        # Zelený proužek = jak daleko je výroba dalšího kusu
        if stroj["pracuje"]:
            delka = int((obdelnik.width - 8) * stroj["cas"] / info["doba"])
            pygame.draw.rect(okno, (120, 255, 120), (obdelnik.x + 4, obdelnik.bottom - 6, delka, 3))

        # Šipka: kam stroj posílá výrobky
        stred_x, stred_y = stred_policka(x2, y2)
        dx, dy = SMERY[stroj["smer"]]
        nakresli_sipku(stred_x + dx * 15, stred_y + dy * 15, stroj["smer"], BILA)


def nakresli_nahled(druh, x, y):
    """Pod myší ukáže, kam se stavba postaví: zelený rámeček = jde to, červený = nejde."""
    if proc_nejde_stavet(druh, x, y) == "":
        barva = (80, 255, 80)
    else:
        barva = (255, 70, 70)
    for px, py in policka_stavby(druh, x, y, smer):
        if je_na_mape(px, py):
            pygame.draw.rect(okno, barva, (px * DLAZDICE, LISTA + py * DLAZDICE, DLAZDICE, DLAZDICE), 3)
    posledni_x, posledni_y = policka_stavby(druh, x, y, smer)[-1]
    stred_x, stred_y = stred_policka(posledni_x, posledni_y)
    nakresli_sipku(stred_x, stred_y, smer, barva)


def nakresli_hrace():
    """Nakreslí hráče (čtverec s očima) a bílý rámeček kolem políčka, na kterém stojí."""
    pygame.draw.rect(okno, BILA, (hrac_sloupec * DLAZDICE, LISTA + hrac_radek * DLAZDICE, DLAZDICE, DLAZDICE), 2)
    telo = pygame.Rect(int(hrac_x), int(hrac_y), VELIKOST_HRACE, VELIKOST_HRACE)
    pygame.draw.rect(okno, BARVY_HRACE[volby["barva"]], telo, border_radius=8)
    pygame.draw.rect(okno, CERNA, telo, 2, border_radius=8)
    pygame.draw.circle(okno, BILA, (telo.x + 9, telo.y + 11), 4)       # oči
    pygame.draw.circle(okno, BILA, (telo.x + 19, telo.y + 11), 4)
    pygame.draw.circle(okno, CERNA, (telo.x + 10, telo.y + 12), 2)
    pygame.draw.circle(okno, CERNA, (telo.x + 20, telo.y + 12), 2)


def nakresli_listu():
    """Horní pruh: čas, body, inventář a lišta se stavbami."""
    pygame.draw.rect(okno, (15, 15, 22), (0, 0, SIRKA, LISTA))
    pygame.draw.line(okno, (90, 80, 150), (0, LISTA - 1), (SIRKA, LISTA - 1), 2)

    # 1. řádek: čas, body, inventář
    sekundy = int(zbyva)
    if sekundy <= 10:
        barva_casu = CERVENA         # posledních 10 sekund je čas červeně
    else:
        barva_casu = BILA
    okno.blit(font_velky.render(f"Čas {sekundy // 60}:{sekundy % 60:02d}", True, barva_casu), (15, 8))
    okno.blit(font_velky.render(f"Body {spocitej_body(odevzdano)}", True, ZLUTA), (165, 8))
    x = 340
    for nazev in ["ruda", "ingot", "plech"]:
        nakresli_predmet(nazev, x, 22)
        okno.blit(font_velky.render(str(inventar[nazev]), True, BILA), (x + 15, 8))
        x += 90
    if volby["fps"] == 1:
        okno.blit(font_maly.render(f"FPS: {int(hodiny.get_fps())}", True, ZELENA), (SIRKA - 80, 10))

    # 2. řádek: stavby 1–4 (vybraná svítí) a směr stavění
    for i in range(len(STAVBY)):
        druh = STAVBY[i]
        if druh == "pas":
            nazev, cena, barva = "Pás", CENA_PASU, (150, 150, 160)
        else:
            nazev, cena, barva = STROJE[druh]["nazev"], STROJE[druh]["cena"], STROJE[druh]["barva"]
        box = pygame.Rect(15 + i * 170, 42, 160, 30)
        if vybrano == druh:
            pygame.draw.rect(okno, (70, 65, 120), box, border_radius=6)
            pygame.draw.rect(okno, FIALOVA, box, 2, border_radius=6)
        else:
            pygame.draw.rect(okno, (35, 35, 50), box, border_radius=6)
        pygame.draw.rect(okno, barva, (box.x + 8, box.y + 8, 14, 14), border_radius=3)
        okno.blit(font_maly.render(f"{i + 1}  {nazev} ({cena})", True, BILA), (box.x + 30, box.y + 6))
    okno.blit(font_maly.render(f"Směr: {SIPKY[smer]}   (R otočit)", True, BILA), (710, 48))


def nakresli_spodek():
    """Dole: zpráva pro hráče a řádek s ovládáním (když je zapnutý v Nastavení)."""
    if zprava != "":
        obrazek = font_stredni.render(zprava, True, ZLUTA)
        ram = obrazek.get_rect(center=(SIRKA // 2, VYSKA - 50))
        pygame.draw.rect(okno, CERNA, ram.inflate(24, 10), border_radius=8)
        okno.blit(obrazek, ram)
    if volby["napoveda"] == 1:
        pygame.draw.rect(okno, (10, 10, 15), (0, VYSKA - 24, SIRKA, 24))
        text = ("WASD pohyb  |  E těžit / obsloužit stroj / sebrat z pásu / odeslat  |  "
                "1–4 vybrat stavbu  |  levé tlačítko postavit (pás jde táhnout)  |  R otočit  |  "
                "pravé tlačítko zbourat  |  Esc zpět")
        okno.blit(font_maly.render(text, True, SEDA), (10, VYSKA - 21))


# =====================================================================
#  8) HLAVNÍ SMYČKA
# =====================================================================

nacti_volby()
nastav_hlasitost()
if hudba_funguje:
    pygame.mixer.music.play(-1)       # hudba hraje pořád dokola


def otevri_okno():
    """Otevře okno hry – podle voleb normálně, nebo přes celou obrazovku."""
    if volby["cela"] == 1:
        return pygame.display.set_mode((SIRKA, VYSKA), pygame.FULLSCREEN)
    return pygame.display.set_mode((SIRKA, VYSKA))


okno = otevri_okno()
pygame.display.set_caption("Astrallift")
hodiny = pygame.time.Clock()
font_velky = pygame.font.SysFont("arial", 24, bold=True)
font_stredni = pygame.font.SysFont("arial", 22)
font_maly = pygame.font.SysFont("arial", 15, bold=True)
font_nadpis = pygame.font.SysFont("arial", 72, bold=True)

# Kdo hraje? ("" = nikdo není přihlášený -> skóre se neuloží)
jmeno_hrace = zjisti_prihlaseneho_hrace()

# Tlačítka v hlavním menu
tl_hrat_1 = Tlacitko("Hrát – 1 minuta", SIRKA // 2, 235)
tl_hrat_3 = Tlacitko("Hrát – 3 minuty", SIRKA // 2, 295)
tl_hrat_5 = Tlacitko("Hrát – 5 minut", SIRKA // 2, 355)
tl_nastaveni = Tlacitko("Nastavení", SIRKA // 2, 430)
tl_ovladani = Tlacitko("Ovládání", SIRKA // 2, 490)
tl_web = Tlacitko("Web – výsledky", SIRKA // 2, 550)
tl_konec = Tlacitko("Konec", SIRKA // 2, 610)

# Tlačítka v nastavení (vpravo vedle popisků)
tl_hudba_minus = Tlacitko("−", 730, 170, 50, 44)
tl_hudba_plus = Tlacitko("+", 910, 170, 50, 44)
tl_cela = Tlacitko("", 820, 232, 180, 44)
tl_fps = Tlacitko("", 820, 294, 180, 44)
tl_mrizka = Tlacitko("", 820, 356, 180, 44)
tl_napoveda = Tlacitko("", 820, 418, 180, 44)
tl_barva = Tlacitko("", 820, 480, 180, 44)
tl_zpet = Tlacitko("Zpět", SIRKA // 2, 650, 220, 50)

# Tlačítka na obrazovce konce hry
tl_do_menu = Tlacitko("Zpět do menu", SIRKA // 2 - 200, 560, 340, 54)
tl_vysledky = Tlacitko("Výsledky na webu", SIRKA // 2 + 200, 560, 340, 54)

# Proměnné rozehrané hry (nastaví se znovu při každém startu hry)
mapa = nova_mapa()
stroje = []                                         # seznam všech strojů
inventar = {"ruda": 0, "ingot": 0, "plech": 0}      # co hráč nese
odevzdano = {"ruda": 0, "ingot": 0, "plech": 0}     # co už odešlo výtahem
hrac_x = 640                                        # pozice hráče v pixelech
hrac_y = 400
hrac_sloupec = 0                                    # políčko, na kterém hráč stojí
hrac_radek = 0
delka_hry = 1                                       # v minutách
zbyva = 60                                          # zbývající čas v sekundách
vybrano = None                                      # co se bude stavět (None = nic)
smer = 0                                            # směr stavění (index do SMERY)
zprava = ""                                         # zpráva dole na obrazovce
zprava_cas = 0                                      # jak dlouho se zpráva ještě ukazuje
ulozeno = ""                                        # text o uložení výsledku (konec hry)
predchozi_stav = "menu"                             # kam se vrátit z obrazovky Ovládání

# Stav = jaká obrazovka je zrovna vidět: "menu", "nastaveni", "ovladani", "hra", "konec"
stav = "menu"
bezi = True

while bezi:
    dt = hodiny.tick(FPS) / 1000        # kolik sekund uběhlo od minulého snímku
    udalosti = pygame.event.get()
    for udalost in udalosti:
        if udalost.type == pygame.QUIT:  # křížek okna
            bezi = False

    okno.fill(POZADI)

    # -----------------------------------------------------------------
    #  HLAVNÍ MENU
    # -----------------------------------------------------------------
    if stav == "menu":
        for udalost in udalosti:
            # Start hry: nastavíme všechno na začátek
            minuty = 0
            if tl_hrat_1.kliknuto(udalost):
                minuty = 1
            if tl_hrat_3.kliknuto(udalost):
                minuty = 3
            if tl_hrat_5.kliknuto(udalost):
                minuty = 5
            if minuty > 0:
                delka_hry = minuty
                zbyva = minuty * 60
                mapa = nova_mapa()
                stroje = []
                inventar = {"ruda": 0, "ingot": 0, "plech": 0}
                odevzdano = {"ruda": 0, "ingot": 0, "plech": 0}
                hrac_x = 640
                hrac_y = 400
                vybrano = None
                smer = 0
                zprava = "Jdi na rudu (vlevo) a těž klávesou E. Pak stav: klávesy 1–4 a myš."
                zprava_cas = 5
                stav = "hra"

            if tl_nastaveni.kliknuto(udalost):
                stav = "nastaveni"
            if tl_ovladani.kliknuto(udalost):
                predchozi_stav = "menu"
                stav = "ovladani"
            if tl_web.kliknuto(udalost):
                webbrowser.open(ADRESA_WEBU + "/vysledky")   # otevře web v prohlížeči (musí běžet web/app.py)
            if tl_konec.kliknuto(udalost):
                bezi = False

        napis("ASTRALLIFT", font_nadpis, FIALOVA, (SIRKA // 2, 105))
        napis("Vytěž, zpracuj a pošli výtahem do vesmíru co nejvíc železa!", font_stredni, BILA, (SIRKA // 2, 165))
        for tlacitko in [tl_hrat_1, tl_hrat_3, tl_hrat_5, tl_nastaveni, tl_ovladani, tl_web, tl_konec]:
            tlacitko.nakresli()
        if jmeno_hrace != "":
            napis(f"Přihlášen: {jmeno_hrace}", font_stredni, ZELENA, (SIRKA // 2, 675))
        else:
            napis("Nepřihlášen – skóre se neuloží. Pro ukládání spusť hru z webu (tlačítko Hrát).",
                  font_stredni, (240, 150, 120), (SIRKA // 2, 675))

    # -----------------------------------------------------------------
    #  NASTAVENÍ
    # -----------------------------------------------------------------
    elif stav == "nastaveni":
        for udalost in udalosti:
            if tl_hudba_minus.kliknuto(udalost):
                volby["hudba"] = max(0, volby["hudba"] - 10)
            if tl_hudba_plus.kliknuto(udalost):
                volby["hudba"] = min(100, volby["hudba"] + 10)
            if tl_cela.kliknuto(udalost):
                volby["cela"] = 1 - volby["cela"]          # 1 - 0 = 1 a 1 - 1 = 0 -> přepne
                okno = otevri_okno()
            if tl_fps.kliknuto(udalost):
                volby["fps"] = 1 - volby["fps"]
            if tl_mrizka.kliknuto(udalost):
                volby["mrizka"] = 1 - volby["mrizka"]
            if tl_napoveda.kliknuto(udalost):
                volby["napoveda"] = 1 - volby["napoveda"]
            if tl_barva.kliknuto(udalost):
                volby["barva"] = (volby["barva"] + 1) % len(BARVY_HRACE)   # další barva dokola
            if tl_zpet.kliknuto(udalost):
                stav = "menu"
            if udalost.type == pygame.KEYDOWN and udalost.key == pygame.K_ESCAPE:
                stav = "menu"
            if udalost.type == pygame.MOUSEBUTTONDOWN:     # po každém kliknutí uložíme
                nastav_hlasitost()
                uloz_volby()

        # Texty na přepínačích podle aktuálních voleb
        tl_cela.text = "ZAP" if volby["cela"] == 1 else "VYP"
        tl_fps.text = "ZAP" if volby["fps"] == 1 else "VYP"
        tl_mrizka.text = "ZAP" if volby["mrizka"] == 1 else "VYP"
        tl_napoveda.text = "ZAP" if volby["napoveda"] == 1 else "VYP"
        tl_barva.text = NAZVY_BAREV[volby["barva"]]

        napis("NASTAVENÍ", font_nadpis, FIALOVA, (SIRKA // 2, 80))
        popisky = ["Hlasitost hudby", "Celá obrazovka", "Ukazovat FPS",
                   "Mřížka na mapě", "Nápověda ve hře", "Barva hráče"]
        for i in range(len(popisky)):
            okno.blit(font_stredni.render(popisky[i], True, BILA), (340, 157 + i * 62))
        napis(f"{volby['hudba']} %", font_stredni, BILA, (820, 170))
        pygame.draw.rect(okno, BARVY_HRACE[volby["barva"]], (930, 466, 28, 28), border_radius=6)
        for tlacitko in [tl_hudba_minus, tl_hudba_plus, tl_cela,
                         tl_fps, tl_mrizka, tl_napoveda, tl_barva, tl_zpet]:
            tlacitko.nakresli()

    # -----------------------------------------------------------------
    #  OVLÁDÁNÍ
    # -----------------------------------------------------------------
    elif stav == "ovladani":
        for udalost in udalosti:
            if tl_zpet.kliknuto(udalost):
                stav = predchozi_stav
            if udalost.type == pygame.KEYDOWN and udalost.key == pygame.K_ESCAPE:
                stav = predchozi_stav

        napis("OVLÁDÁNÍ", font_nadpis, FIALOVA, (SIRKA // 2, 70))
        radky = [
            ["W A S D / šipky", "pohyb postavy"],
            ["E", "na rudě vytěžíš rudu, u stroje vybereš výrobky a vložíš suroviny"],
            ["", "na pásu sebereš věc, ve výtahu odešleš vše, co neseš"],
            ["1 / 2 / 3 / 4", "vybrat stavbu: Těžič (5 rudy), Pec (10), Lis (15), Pás (1)"],
            ["Levé tlačítko myši", "postavit pod myší (pás: drž tlačítko a táhni)"],
            ["R", "otočit směr stavby (šipka = kam stroj nebo pás posílá věci)"],
            ["Pravé tlačítko myši", "zbourat (ruda i obsah se vrátí)"],
            ["Esc", "zrušit výběr stavby / zpět do menu"],
        ]
        y = 140
        for klavesa, popis in radky:
            okno.blit(font_velky.render(klavesa, True, ZLUTA), (90, y))
            okno.blit(font_stredni.render(popis, True, BILA), (360, y + 2))
            y += 40
        tipy = [
            "Body za kus: ruda 1, ingot 2, plech 4. Počítá se jen to, co odejde výtahem.",
            "Těžič (1×1) stojí na rudě. Pec a Lis (2×1) ukazují vstup (suroviny) a výstup (výrobky).",
            "Stroje posílají výrobky tam, kam míří šipka. Pás je doveze do stroje nebo do výtahu.",
        ]
        for tip in tipy:
            y += 34
            napis(tip, font_stredni, SEDA, (SIRKA // 2, y))
        tl_zpet.nakresli()

    # -----------------------------------------------------------------
    #  HRA
    # -----------------------------------------------------------------
    elif stav == "hra":
        # Na jakém políčku je myš a na jakém hráč
        mys_x, mys_y = pygame.mouse.get_pos()
        mys_sloupec = mys_x // DLAZDICE
        mys_radek = (mys_y - LISTA) // DLAZDICE
        hrac_sloupec = int((hrac_x + VELIKOST_HRACE / 2) // DLAZDICE)
        hrac_radek = int((hrac_y + VELIKOST_HRACE / 2 - LISTA) // DLAZDICE)

        # --- 1. Vstupy (klávesy a myš) ---
        for udalost in udalosti:
            if udalost.type == pygame.KEYDOWN:
                if udalost.key == pygame.K_ESCAPE:
                    if vybrano is not None:
                        vybrano = None                  # první Esc zruší výběr stavby
                    else:
                        stav = "menu"                   # druhý Esc = zpět do menu (nic se neuloží)
                elif udalost.key == pygame.K_e:
                    zprava = stiskni_e(hrac_sloupec, hrac_radek)
                    zprava_cas = 2.5
                elif udalost.key == pygame.K_r:
                    smer = (smer + 1) % 4               # další směr dokola
                elif udalost.key == pygame.K_q:
                    vybrano = None
                elif udalost.key in KLAVESY_STAVEB:
                    druh = KLAVESY_STAVEB[udalost.key]
                    if vybrano == druh:
                        vybrano = None                  # druhý stisk stejné klávesy výběr zruší
                    else:
                        vybrano = druh

            if udalost.type == pygame.MOUSEBUTTONDOWN:
                if udalost.button == 1 and vybrano is not None:     # levé tlačítko = stavět
                    duvod = proc_nejde_stavet(vybrano, mys_sloupec, mys_radek)
                    if duvod == "":
                        postav(vybrano, mys_sloupec, mys_radek)
                        zprava = "Postaveno."
                    else:
                        zprava = duvod
                    zprava_cas = 2.5
                if udalost.button == 3:                             # pravé tlačítko = bourat
                    zprava = zbourej(mys_sloupec, mys_radek)
                    zprava_cas = 2.5

        # Pás se dá pokládat i tažením myši (držíš levé tlačítko)
        if vybrano == "pas" and pygame.mouse.get_pressed()[0]:
            if proc_nejde_stavet("pas", mys_sloupec, mys_radek) == "":
                postav("pas", mys_sloupec, mys_radek)

        # Pohyb hráče (držené klávesy)
        klavesy = pygame.key.get_pressed()
        if klavesy[pygame.K_a] or klavesy[pygame.K_LEFT]:
            hrac_x -= RYCHLOST_HRACE * dt
        if klavesy[pygame.K_d] or klavesy[pygame.K_RIGHT]:
            hrac_x += RYCHLOST_HRACE * dt
        if klavesy[pygame.K_w] or klavesy[pygame.K_UP]:
            hrac_y -= RYCHLOST_HRACE * dt
        if klavesy[pygame.K_s] or klavesy[pygame.K_DOWN]:
            hrac_y += RYCHLOST_HRACE * dt
        hrac_x = max(0, min(hrac_x, SIRKA - VELIKOST_HRACE))      # nesmí utéct z mapy
        hrac_y = max(LISTA, min(hrac_y, VYSKA - VELIKOST_HRACE))

        # --- 2. Logika ---
        aktualizuj_stroje(dt)
        aktualizuj_pasy(dt)
        zbyva -= dt
        zprava_cas -= dt
        if zprava_cas <= 0:
            zprava = ""

        # Konec hry: uložíme výsledek (jen když je hráč přihlášený)
        if zbyva <= 0:
            skore = spocitej_body(odevzdano)
            if jmeno_hrace == "":
                ulozeno = "Nejsi přihlášený, výsledek se neukládá. Spusť hru z webu."
            elif uloz_do_databaze(jmeno_hrace, delka_hry, skore, odevzdano):
                ulozeno = "Výsledek je uložený v databázi."
            else:
                ulozeno = "Výsledek se NEPODAŘILO uložit (databáze? pripojeni.py?)."
            stav = "konec"

        # --- 3. Kreslení ---
        nakresli_mapu()
        nakresli_pasy()
        nakresli_stroje()
        if vybrano is not None and je_na_mape(mys_sloupec, mys_radek):
            nakresli_nahled(vybrano, mys_sloupec, mys_radek)
        nakresli_hrace()
        nakresli_listu()
        nakresli_spodek()

    # -----------------------------------------------------------------
    #  KONEC HRY
    # -----------------------------------------------------------------
    elif stav == "konec":
        for udalost in udalosti:
            if tl_do_menu.kliknuto(udalost):
                stav = "menu"
            if tl_vysledky.kliknuto(udalost):
                webbrowser.open(ADRESA_WEBU + "/vysledky")
            if udalost.type == pygame.KEYDOWN and udalost.key == pygame.K_RETURN:
                stav = "menu"

        napis("ČAS VYPRŠEL", font_nadpis, FIALOVA, (SIRKA // 2, 160))
        napis(f"Body: {spocitej_body(odevzdano)}", font_velky, ZLUTA, (SIRKA // 2, 270))
        napis(f"Odesláno: ruda {odevzdano['ruda']}, ingot {odevzdano['ingot']}, plech {odevzdano['plech']}",
              font_stredni, BILA, (SIRKA // 2, 320))
        napis(ulozeno, font_stredni, SEDA, (SIRKA // 2, 400))
        tl_do_menu.nakresli()
        tl_vysledky.nakresli()

    pygame.display.flip()

pygame.quit()
