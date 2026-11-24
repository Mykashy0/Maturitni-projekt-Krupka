# Jak spustit Astrallift ve VS Code

Návod krok za krokem. Stačí to udělat jednou, příště už jen kroky 5 a 6.

---

## 1. Otevři projekt

Ve VS Code: **File → Open Folder…** a vyber složku `Projekt`
(ta, ve které je `hra.py` a složka `web`).

## 2. Otevři terminál

Menu **Terminal → New Terminal** (nebo zkratka `Ctrl + ;`).
Dole se otevře okno, kam se píšou příkazy.

## 3. Vyber správný Python

Na tomhle počítači jsou dva Pythony a jen jeden má všechny knihovny.

1. Stiskni `Ctrl + Shift + P`
2. Napiš **Python: Select Interpreter** a potvrď Enterem
3. Vyber **Python 3.12**

V terminálu vždy piš `python`, nikdy `py` (to spouští jiný Python).

## 4. Nainstaluj knihovny (jen poprvé)

Do terminálu napiš:

```
pip install -r requirements.txt
```

Nainstaluje se pygame (hra), flask (web), mysql-connector-python (databáze) a bcrypt (hesla).

## 5. Zkontroluj soubor `pripojeni.py`

Ve složce `Projekt` musí být soubor `pripojeni.py` s údaji k databázi:

```python
HOST = "dbs.spskladno.cz"
USER = "student14"
PASSWORD = "tvoje_heslo"
DATABASE = "vyuka14"
```

Když chybí, vytvoř ho (**File → New File**, ulož jako `pripojeni.py`).
Na GitHub se neposílá, takže na novém počítači ho musíš vytvořit znovu.

## 6. Spusť web

Do terminálu napiš:

```
python web/app.py
```

Až uvidíš `Running on http://127.0.0.1:5000`, otevři v prohlížeči:

**http://127.0.0.1:5000**

Terminál nech otevřený! Když ho zavřeš (nebo dáš `Ctrl + C`), web přestane fungovat.

## 7. Hraj

1. Na webu klikni vpravo nahoře na **Přihlásit / Registrace**
2. Zaregistruj se (jméno aspoň 3 znaky, heslo aspoň 6 znaků)
3. Na úvodní stránce klikni na **▶ Hrát**, otevře se okno hry
4. V menu hry vyber délku hry (1, 3 nebo 5 minut)
5. Po konci hry se skóre uloží a uvidíš ho na webu v **Výsledcích**

Na zkoušku jde použít i vzorový účet: jméno **Pepa**, heslo **heslo123**.

---

## Spuštění jen hry (bez webu)

Otevři `hra.py` a klikni na ▷ vpravo nahoře, nebo napiš do terminálu:

```
python hra.py
```

Hrát jde, ale skóre se **neuloží**, protože nikdo není přihlášený.

---

## Když něco nejde

| Co vidíš | Co s tím |
|----------|----------|
| `No module named 'pygame'` (nebo flask, bcrypt…) | Udělej krok 3 a 4 znovu. |
| `No module named 'pripojeni'` | Chybí `pripojeni.py`, viz krok 5. |
| Web píše „Databáze není dostupná“ | Špatné údaje v `pripojeni.py`, nebo nejsi ve školní síti. |
| Prohlížeč píše „Nelze se připojit“ | Web neběží, spusť znovu krok 6. |
| Stránka nemá barvy a vypadá hnusně | Neotvírej `.html` dvojklikem, vždy přes http://127.0.0.1:5000 |
| Port 5000 je obsazený | Web už běží v jiném terminálu, zavři ho, nebo jen otevři prohlížeč. |
| Hra je potichu | V Nastavení hry zvyš hlasitost hudby. |

## Soubory, které si program vytvoří sám

| Soubor | K čemu je |
|--------|-----------|
| `volby.txt` | nastavení hry (hlasitost, barva hráče…) |
| `prihlaseny.txt` | jméno hráče, které web předá hře při kliknutí na Hrát |

Oba jdou klidně smazat, nic se nerozbije.
