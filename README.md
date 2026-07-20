# ⛽ Capo Nord 2026 · prezzi benzina automatici

Questo mini-repo aggiorna ogni mattina `prices.json` con i prezzi della benzina
lungo la rotta Torino → Capo Nord, e il sito del viaggio lo legge da solo.

## Come si monta (5 minuti)

1. **Crea un repository PUBBLICO** su GitHub, ad esempio `caponord-prezzi`
   (deve essere pubblico, altrimenti il sito non può leggere il file raw).
2. **Carica questi file** rispettando le cartelle:
   - `prices.json`
   - `scripts/update_prices.py`
   - `.github/workflows/update-prices.yml`
   (puoi trascinarli dall'interfaccia web: *Add file → Upload files*).
3. **Permessi di scrittura al bot**: nel repo vai su
   *Settings → Actions → General → Workflow permissions* e seleziona
   **"Read and write permissions"**, poi salva.
4. **Primo lancio a mano**: tab *Actions* → workflow **"Aggiorna prezzi benzina"**
   → pulsante **"Run workflow"**. Dopo ~1 minuto controlla che `prices.json`
   abbia la data di oggi in `updated`.
5. **Copia il link RAW**: apri `prices.json` nel repo, premi il bottone **Raw**
   e copia l'indirizzo. Ha questa forma:
   `https://raw.githubusercontent.com/TUO-UTENTE/caponord-prezzi/main/prices.json`
6. **Incollalo nel sito**: sezione **Benzina** → campo
   "URL di prices.json su GitHub" → **Collega**. Fatto: il collegamento è
   condiviso, quindi vale automaticamente anche per Vale e Ale.

Da quel momento il workflow gira ogni giorno alle **07:30 italiane** e il sito,
a ogni apertura, scarica i prezzi freschi e ricalcola la media ponderata.

## Cosa viene aggiornato e cosa no

| Paesi | Fonte | Frequenza |
|---|---|---|
| 🇮🇹 Italia | Open data MIMIT (media nazionale self) | Giornaliera |
| 🇩🇪 🇩🇰 🇸🇪 🇫🇮 🇪🇪 🇱🇻 🇱🇹 🇵🇱 | Bollettino Petrolifero UE | Settimanale |
| 🇳🇴 Norvegia · 🇨🇭 Svizzera | Nessuna fonte gratuita | A mano nel sito |

Se una fonte non risponde, restano gli ultimi valori validi: il sito non
rimane mai senza prezzi. Se la Commissione UE cambia l'indirizzo del
bollettino (capita), basta aggiornare la lista `EU_URLS` in cima a
`scripts/update_prices.py`.
