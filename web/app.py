# =====================================================================
#  ASTRALLIFT – WEB (Flask)
#
#  Spuštění (ze složky Projekt):  python web/app.py
#  Pak otevři v prohlížeči:       http://127.0.0.1:5000
#
#  Celý web je v tomhle jednom souboru:
#    - databáze: vytvoření tabulek, vzorová data a dotazy (SQL přímo tady)
#    - stránky: O hře, Výsledky, Autor, Přihlášení/Registrace
#    - přihlášení, registrace, odhlášení (hesla přes bcrypt)
#    - tlačítko Hrát: spustí hru pro přihlášeného hráče
#  HTML stránky jsou ve složce templates, vzhled ve static/styly.css
# =====================================================================

import os
import subprocess
import sys
import bcrypt
import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session

# Složka Projekt (o složku výš než tento soubor). Je v ní hra.py, pripojeni.py a prihlaseny.txt.
SLOZKA_PROJEKTU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Soubor pripojeni.py je ve složce Projekt (sdílí ho web i hra) -> řekneme Pythonu, ať hledá i tam
sys.path.append(SLOZKA_PROJEKTU)
from pripojeni import *            # HOST, USER, PASSWORD, DATABASE

app = Flask(__name__)
app.secret_key = "astrallift_tajny_klic"     # potřeba pro session (přihlášení)


def pripoj():
    """Připojí se k databázi. Údaje jsou v souboru pripojeni.py."""
    return mysql.connector.connect(host=HOST, user=USER, password=PASSWORD, database=DATABASE)


# ---------------------------------------------------------------------
#  DATABÁZE – vytvoření tabulek a vzorová data
#  Všechny tabulky mají předponu ast_, aby se nepletly s jinými
#  tabulkami ve sdílené školní databázi.
# ---------------------------------------------------------------------

def vytvor_tabulky():
    """Vytvoří tabulky (když ještě nejsou) a vloží předměty a vzorová data."""
    mydb = pripoj()
    mycursor = mydb.cursor()

    # Hráči (účty z webu). Heslo je uložené jako hash (bcrypt), nikdy ne čitelně.
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS ast_hraci (
            id INT AUTO_INCREMENT PRIMARY KEY,
            jmeno VARCHAR(30) NOT NULL UNIQUE,
            heslo VARCHAR(255) NULL,
            registrovan DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")

    # Předměty, které se dají odeslat výtahem, a kolik za ně je bodů
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS ast_predmety (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nazev VARCHAR(30) NOT NULL UNIQUE,
            body INT NOT NULL DEFAULT 1
        )""")

    # Odehrané hry – vztah 1:N (jeden hráč má hodně her)
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS ast_hry (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hrac_id INT NOT NULL,
            delka_minut INT NOT NULL DEFAULT 3,
            skore INT NOT NULL DEFAULT 0,
            datum DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hrac_id) REFERENCES ast_hraci(id) ON DELETE CASCADE
        )""")

    # Co se v které hře odeslalo – vztah M:N mezi hrami a předměty
    mycursor.execute("""
        CREATE TABLE IF NOT EXISTS ast_odevzdane_predmety (
            hra_id INT NOT NULL,
            predmet_id INT NOT NULL,
            pocet INT NOT NULL DEFAULT 0,
            PRIMARY KEY (hra_id, predmet_id),
            FOREIGN KEY (hra_id) REFERENCES ast_hry(id) ON DELETE CASCADE,
            FOREIGN KEY (predmet_id) REFERENCES ast_predmety(id)
        )""")

    # Předměty (body musí sedět s BODY v hra.py) – jen když tabulka je prázdná
    mycursor.execute("SELECT COUNT(*) FROM ast_predmety")
    if mycursor.fetchone()[0] == 0:
        mycursor.execute("INSERT INTO ast_predmety (nazev, body) VALUES ('ruda', 1), ('ingot', 2), ('plech', 4)")

    # Vzorová data – jen když v databázi ještě nejsou žádní hráči
    mycursor.execute("SELECT COUNT(*) FROM ast_hraci")
    if mycursor.fetchone()[0] == 0:
        vloz_vzorova_data(mycursor)

    mydb.commit()
    mydb.close()


def vloz_vzorova_data(mycursor):
    """Vloží 3 vzorové hráče (všichni mají heslo heslo123) a jejich hry."""
    hash_hesla = bcrypt.hashpw("heslo123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    mycursor.execute("INSERT INTO ast_hraci (jmeno, heslo) VALUES (%s, %s), (%s, %s), (%s, %s)",
                     ("Hrac1", hash_hesla, "Pepa", hash_hesla, "Lucka", hash_hesla))

    # Vzorové hry: (jméno hráče, délka v minutách, kolik rudy, ingotů a plechů odeslal)
    vzorove_hry = [("Hrac1", 1, 25, 0, 0), ("Pepa", 3, 40, 40, 0), ("Lucka", 3, 20, 30, 18)]
    for jmeno, minuty, ruda, ingot, plech in vzorove_hry:
        skore = ruda * 1 + ingot * 2 + plech * 4

        mycursor.execute("SELECT id FROM ast_hraci WHERE jmeno = %s", (jmeno,))
        hrac_id = mycursor.fetchone()[0]
        mycursor.execute("INSERT INTO ast_hry (hrac_id, delka_minut, skore) VALUES (%s, %s, %s)",
                         (hrac_id, minuty, skore))
        mycursor.execute("SELECT MAX(id) FROM ast_hry WHERE hrac_id = %s", (hrac_id,))
        hra_id = mycursor.fetchone()[0]

        for nazev, pocet in [("ruda", ruda), ("ingot", ingot), ("plech", plech)]:
            if pocet > 0:
                mycursor.execute("SELECT id FROM ast_predmety WHERE nazev = %s", (nazev,))
                predmet_id = mycursor.fetchone()[0]
                mycursor.execute("INSERT INTO ast_odevzdane_predmety (hra_id, predmet_id, pocet) "
                                 "VALUES (%s, %s, %s)", (hra_id, predmet_id, pocet))


# ---------------------------------------------------------------------
#  STRÁNKY
#  Každá stránka dostane jmeno = přihlášený hráč (nebo None),
#  aby navigace věděla, jestli ukázat "Přihlásit" nebo "Odhlásit".
# ---------------------------------------------------------------------

@app.route("/")
def index():
    """Úvodní stránka: o hře, pravidla a tlačítko Hrát."""
    return render_template("index.html", jmeno=session.get("jmeno"))


@app.route("/autor")
def autor():
    """Stránka o autorovi."""
    return render_template("autor.html", jmeno=session.get("jmeno"))


@app.route("/vysledky")
def vysledky():
    """Výsledky z databáze: žebříček her, nejlepší hráči, moje hry. Jde i hledat hráče."""
    hledat = request.args.get("hledat", "")     # text z políčka Hledat (z adresy ?hledat=...)
    zebricek = []
    nejlepsi_hraci = []
    moje_hry = []
    chyba = None
    try:
        mydb = pripoj()
        mycursor = mydb.cursor()

        # 20 nejlepších her (JOIN + WHERE LIKE + ORDER BY). % znamená "cokoliv".
        mycursor.execute("""
            SELECT ast_hraci.jmeno, ast_hry.skore, ast_hry.delka_minut, ast_hry.datum
            FROM ast_hry
            JOIN ast_hraci ON ast_hraci.id = ast_hry.hrac_id
            WHERE ast_hraci.jmeno LIKE %s
            ORDER BY ast_hry.skore DESC
            LIMIT 20""", ("%" + hledat + "%",))
        zebricek = mycursor.fetchall()

        # Nejlepší skóre a počet her každého hráče (GROUP BY)
        mycursor.execute("""
            SELECT ast_hraci.jmeno, MAX(ast_hry.skore), COUNT(ast_hry.id)
            FROM ast_hraci
            JOIN ast_hry ON ast_hry.hrac_id = ast_hraci.id
            GROUP BY ast_hraci.jmeno
            ORDER BY MAX(ast_hry.skore) DESC""")
        nejlepsi_hraci = mycursor.fetchall()

        # Hry přihlášeného hráče od nejnovější (WHERE + ORDER BY)
        if "jmeno" in session:
            mycursor.execute("""
                SELECT ast_hry.skore, ast_hry.delka_minut, ast_hry.datum
                FROM ast_hry
                JOIN ast_hraci ON ast_hraci.id = ast_hry.hrac_id
                WHERE ast_hraci.jmeno = %s
                ORDER BY ast_hry.datum DESC""", (session["jmeno"],))
            moje_hry = mycursor.fetchall()

        mydb.close()
    except mysql.connector.Error as e:
        chyba = f"Databáze není dostupná: {e}"

    return render_template("vysledky.html", jmeno=session.get("jmeno"), hledat=hledat,
                           zebricek=zebricek, nejlepsi_hraci=nejlepsi_hraci,
                           moje_hry=moje_hry, chyba=chyba)


# ---------------------------------------------------------------------
#  PŘIHLÁŠENÍ, REGISTRACE, ODHLÁŠENÍ
# ---------------------------------------------------------------------

@app.route("/prihlaseni", methods=["GET", "POST"])
def prihlaseni():
    """Přihlášení. Na stejné stránce je i formulář pro registraci."""
    if request.method == "POST":
        jmeno = request.form["jmeno"]
        heslo = request.form["heslo"]
        try:
            mydb = pripoj()
            mycursor = mydb.cursor()
            mycursor.execute("SELECT jmeno, heslo FROM ast_hraci WHERE jmeno = %s", (jmeno,))
            hrac = mycursor.fetchone()          # (jmeno, heslo) nebo None
            mydb.close()
        except mysql.connector.Error as e:
            return render_template("prihlaseni.html", jmeno=None, chyba=f"Databáze není dostupná: {e}")

        # Hráč existuje a heslo sedí? (bcrypt porovná heslo s uloženým hashem)
        spravne = False
        if hrac is not None and hrac[1] is not None:
            try:
                spravne = bcrypt.checkpw(heslo.encode("utf-8"), hrac[1].encode("utf-8"))
            except ValueError:
                spravne = False             # heslo uložené starým způsobem -> nejde ověřit

        if spravne:
            session["jmeno"] = hrac[0]      # zapamatujeme si přihlášeného hráče
            return redirect(url_for("index"))
        return render_template("prihlaseni.html", jmeno=None, chyba="Špatné jméno nebo heslo.")

    return render_template("prihlaseni.html", jmeno=session.get("jmeno"))


@app.route("/registrace", methods=["POST"])
def registrace():
    """Registrace nového hráče (formulář je na stránce Přihlášení)."""
    jmeno = request.form["jmeno"].strip()
    heslo = request.form["heslo"]

    # Kontrola zadaných údajů
    if len(jmeno) < 3 or len(jmeno) > 30:
        return render_template("prihlaseni.html", jmeno=None, chyba_registrace="Jméno musí mít 3 až 30 znaků.")
    if len(heslo) < 6:
        return render_template("prihlaseni.html", jmeno=None, chyba_registrace="Heslo musí mít aspoň 6 znaků.")

    try:
        mydb = pripoj()
        mycursor = mydb.cursor()

        # Není jméno obsazené?
        mycursor.execute("SELECT id FROM ast_hraci WHERE jmeno = %s", (jmeno,))
        if mycursor.fetchone() is not None:
            mydb.close()
            return render_template("prihlaseni.html", jmeno=None, chyba_registrace="Toto jméno už někdo má.")

        # Uložíme hráče. Heslo zahashujeme (bcrypt), čitelně se nikdy neukládá.
        hash_hesla = bcrypt.hashpw(heslo.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        mycursor.execute("INSERT INTO ast_hraci (jmeno, heslo) VALUES (%s, %s)", (jmeno, hash_hesla))
        mydb.commit()
        mydb.close()
    except mysql.connector.Error as e:
        return render_template("prihlaseni.html", jmeno=None, chyba_registrace=f"Databáze není dostupná: {e}")

    session["jmeno"] = jmeno            # po registraci je hráč rovnou přihlášený
    return redirect(url_for("index"))


@app.route("/odhlaseni")
def odhlaseni():
    """Odhlášení: zapomeneme přihlášeného hráče."""
    session.pop("jmeno", None)
    return redirect(url_for("index"))


# ---------------------------------------------------------------------
#  HRÁT – spustí hru
# ---------------------------------------------------------------------

@app.route("/hrat", methods=["POST"])
def hrat():
    """Spustí hru. Hrát může jen přihlášený hráč (aby se mu uložilo skóre)."""
    if "jmeno" not in session:
        return redirect(url_for("prihlaseni"))

    # Jméno hráče předáme hře přes soubor prihlaseny.txt (hra si ho po spuštění přečte)
    with open(os.path.join(SLOZKA_PROJEKTU, "prihlaseny.txt"), "w", encoding="utf-8") as soubor:
        soubor.write(session["jmeno"])

    # Spustíme hra.py stejným Pythonem, kterým běží web (hra se otevře v novém okně)
    subprocess.Popen([sys.executable, os.path.join(SLOZKA_PROJEKTU, "hra.py")])

    return render_template("index.html", jmeno=session["jmeno"],
                           zprava="Hra se spouští, okno se otevře za chvíli.")


# ---------------------------------------------------------------------
#  START WEBU
# ---------------------------------------------------------------------

if __name__ == "__main__":
    try:
        vytvor_tabulky()
        print("Databáze je připravená.")
    except mysql.connector.Error as e:
        print("POZOR: Databáze není dostupná:", e)
    app.run(debug=True)
