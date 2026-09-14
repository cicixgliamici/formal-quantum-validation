# Guida alla demo del progetto

Questa guida raccoglie i comandi piu utili per presentare Formal Quantum
Validation dal vivo. I comandi PowerShell vanno eseguiti dalla radice del
repository, con l'ambiente Python 3.12 gia installato.

## Preparazione prima dello show

La demo non dovrebbe dipendere da download o installazioni in diretta. Preparare
l'ambiente una volta con:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -c constraints-python312.txt -e ".[dev]"
python -m pip check
lake build
```

Se la policy di PowerShell impedisce l'attivazione, tutti i comandi Python
possono usare direttamente `.\.venv\Scripts\python.exe` al posto di `python`.
Elan puo tentare un download al primo uso: eseguire `lake build` almeno una volta
con rete disponibile prima della presentazione.

Per controllare rapidamente la postazione preparata:

```powershell
python --version
python -m pip check
python -m pytest
lake build
```

Il baseline supportato e Python 3.12. I test Python ordinari non richiedono Coq;
la parte Coq/SQIR richiede invece Linux o WSL e l'ambiente opam descritto nella
[guida di sviluppo](DEVELOPMENT.md#coq-environment).

## Percorso collaudato e risultati attesi

Questa sequenza e stata eseguita con successo su PowerShell in Windows. Serve
come scaletta pronta da copiare durante la presentazione. I conteggi campionati
possono variare leggermente; sono corretti quando ogni controllo termina con
`[PASS]` e il risultato complessivo e `PASS`.

Attivare prima l'ambiente:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Verificare Bell con campionamento riproducibile:

```powershell
fqv-verify --shots 10000 --seed 42
```

Risultato atteso: `Overall result: PASS`, fedelta esatta pari a `1`, probabilita
esatte `0.5` per `00` e `11`, e frequenze campionate vicine a `0.5`. Con seed
`42`, l'esecuzione collaudata ha osservato `5015/10000` per `00` e `4985/10000`
per `11`.

Mostrare il controesempio di fase:

```powershell
fqv-demo-phase
```

Risultato atteso: `Measurement probabilities: PASS` e
`Exact quantum state: FAIL`. In questa demo `FAIL` e il comportamento voluto:
il programma termina con codice zero solo se il contratto esatto rifiuta la fase
relativa errata.

Verificare gli altri casi studio:

```powershell
fqv-verify --ir examples/ghz3_ir.json --contract src/fqv/data/ghz3.contract.json
fqv-verify --ir examples/dj2_constant_ir.json --contract src/fqv/data/dj2_constant.contract.json
fqv-verify --ir examples/dj2_balanced_ir.json --contract src/fqv/data/dj2_balanced.contract.json
```

Risultato atteso: tutti e tre mostrano `Overall result: PASS` e fedelta `1`.
Un errore massimo dell'ordine di `2.22e-16` e normale arrotondamento numerico,
non un fallimento.

Dopo avere generato `build/ShowoffDuplicateH.lean` con la demo di ottimizzazione
descritta sotto, farlo controllare dal kernel Lean e rendere visibile il suo
codice di uscita:

```powershell
lake env lean build/ShowoffDuplicateH.lean
if ($LASTEXITCODE -eq 0) {
    Write-Host "PASS: Lean ha verificato formalmente il certificato" -ForegroundColor Green
} else {
    Write-Host "FAIL: Lean ha rifiutato il certificato" -ForegroundColor Red
}
```

Lean normalmente non stampa nulla quando accetta un singolo file. Il ritorno al
prompt con codice `0`, reso esplicito dal messaggio verde, e il risultato atteso.

Infine controllare tutto lo sviluppo Lean incluso nel repository:

```powershell
lake build
```

Risultato atteso: `Build completed successfully`. Il numero di job mostrato puo
cambiare con la versione del progetto e lo stato della cache; non fa parte della
specifica della demo.

## Demo essenziale: Bell in due minuti

Il comando senza argomenti usa il circuito e il contratto Bell inclusi nel
pacchetto:

```powershell
fqv-verify
```

Per rendere visibili gli input effettivi e produrre artefatti ispezionabili:

```powershell
fqv-verify `
  --ir examples/bell_ir.json `
  --contract src/fqv/data/bell.contract.json `
  --ir-output build/showoff_bell_ir.json `
  --json-report build/showoff_bell_report.json
```

Il terminale mostra un `PASS` complessivo e controlli separati per numero di
qubit, gate, ampiezze esatte, probabilita esatte e campionamento. Aprire poi
`build/showoff_bell_report.json` per mostrare che il risultato e anche
machine-readable. `--shots` e `--seed` permettono di cambiare, o rendere
riproducibile, la parte campionata:

```powershell
fqv-verify --shots 10000 --seed 42
```

## Demo consigliata: ottimizzazione e certificato formale

L'esempio `duplicate_h` contiene due Hadamard adiacenti. Qiskit li elimina e il
progetto controlla sia l'equivalenza dell'operatore completo sia la specifica
riscrittura `H; H -> I`:

```powershell
fqv-verify `
  --ir examples/duplicate_h_ir.json `
  --contract examples/duplicate_h.contract.json `
  --transpile `
  --optimization-level 1 `
  --seed-transpiler 7 `
  --transpiled-ir-output build/showoff_duplicate_h_ir.json `
  --equivalence-report build/showoff_duplicate_h_equivalence.json `
  --transpilation-certificate build/showoff_duplicate_h_certificate.json `
  --transpilation-proof-output build/ShowoffDuplicateH.lean `
  --verification-manifest build/showoff_manifest.json
```

Il risultato piu comunicativo e `Depth: 2 -> 0`, insieme a process fidelity 1,
errore allineato in fase vicino a zero e generazione di tre artefatti. Mostrare:

- `build/showoff_duplicate_h_ir.json`, dove la lista delle operazioni e vuota;
- `build/showoff_duplicate_h_certificate.json`, che conserva sorgente,
  candidato e passo di riscrittura riproducibile;
- `build/ShowoffDuplicateH.lean`, che contiene l'obbligo controllabile dal
  kernel Lean;
- `build/showoff_manifest.json`, che lega input, risultati e artefatti tramite
  hash e dichiara esplicitamente che la prova e stata generata ma non ancora
  accettata dal kernel.

Con Lean gia predisposto, compilare l'obbligo appena generato:

```powershell
lake env lean build/ShowoffDuplicateH.lean
if ($LASTEXITCODE -eq 0) {
    Write-Host "PASS: Lean ha verificato formalmente il certificato" -ForegroundColor Green
} else {
    Write-Host "FAIL: Lean ha rifiutato il certificato" -ForegroundColor Red
}
```

L'assenza di output da `lean` indica normalmente successo, non un blocco. Il
messaggio aggiunto rende l'esito immediatamente leggibile al pubblico.

Lo stesso certificato puo generare un modulo Coq:

```powershell
fqv-verify `
  --ir examples/duplicate_h_ir.json `
  --contract examples/duplicate_h.contract.json `
  --transpile `
  --optimization-level 1 `
  --transpilation-certificate build/showoff_duplicate_h_certificate.json `
  --transpilation-proof-backend coq `
  --transpilation-proof-output build/ShowoffDuplicateH.v
```

Questa certificazione e intenzionalmente limitata alla cancellazione di coppie
adiacenti uguali di porte auto-inverse (`X`, `Z`, `H`, `CNOT`, `SWAP`).
L'equivalenza numerica gestisce piu casi, ma non va presentata come prova
formale generale del transpiler.

Per mostrare un errore che le sole probabilita non rilevano:

```powershell
fqv-demo-phase
```

Il comando termina con successo quando le probabilita di Bell Phi-minus
passano rispetto al contratto Phi-plus ma il controllo dello stato esatto
rifiuta correttamente la fase relativa. La guida dedicata
[relative-phase demo](PHASE_DEMO.md) mostra l'output completo atteso e spiega
il codice di uscita.

## Altri casi studio pronti

Usare lo stesso comando per confrontare casi di dimensione e struttura diverse:

```powershell
fqv-verify --ir examples/ghz3_ir.json --contract src/fqv/data/ghz3.contract.json
fqv-verify --ir examples/dj2_constant_ir.json --contract src/fqv/data/dj2_constant.contract.json
fqv-verify --ir examples/dj2_balanced_ir.json --contract src/fqv/data/dj2_balanced.contract.json
```

- Bell evidenzia la differenza tra ampiezze/stato e sole probabilita di misura.
- GHZ(3) mostra un obbligo generato piu grande; Lean contiene anche il teorema
  parametrico per la famiglia GHZ(n) non vuota. Il primo usa la catena CNOT
  `0 -> 1 -> 2` e una prova sugli otto stati di base; il secondo usa fan-out dal
  qubit zero e induzione per ogni dimensione positiva.
- Deutsch-Jozsa mostra due istanze fisse: oracolo costante zero e oracolo
  bilanciato `f(x0, x1) = x0`.

Non presentare le due istanze Deutsch-Jozsa come una prova dell'algoritmo per
ogni oracolo promesso.

## Generazione esplicita degli obblighi

Per rendere chiaro il confine tra generazione e verifica, generare un file in
`build/` e solo dopo consegnarlo al proof assistant:

```powershell
fqv-generate `
  examples/bell_ir.json `
  src/fqv/data/bell.contract.json `
  build/GeneratedBell.lean
lake env lean build/GeneratedBell.lean
```

Il backend Coq usa gli stessi IR e contratto:

```powershell
fqv-generate `
  examples/bell_ir.json `
  src/fqv/data/bell.contract.json `
  build/GeneratedBell.v `
  --backend coq
```

Generare il sorgente non prova da solo il teorema: l'evidenza formale arriva
solo quando Lean o Coq accetta il modulo.

## Test efficaci da mostrare

Una selezione breve e leggibile:

```powershell
python -m pytest tests/test_contract_pipeline.py -v
python -m pytest tests/test_transpilation_certificate.py -v
python -m pytest tests/test_matrix_properties.py -v
```

La verifica completa Python e Lean:

```powershell
python -m pytest
python -m ruff check src tests coq_tests integration_tests
lake build
python -m pytest integration_tests -v
```

L'integration suite Lean compila obblighi derivati da Qiskit e richiede che un
target deliberatamente falso sia rifiutato. Per una demo Coq preparata in WSL:

```bash
opam exec -- python -m pytest coq_tests/test_coq_compilation.py -v
opam exec -- python -m pytest coq_tests/test_gate_semantics.py -v
```

Il secondo comando e piu lungo: verifica le semantiche dei gate su basi
indipendenti ed e adatto a una sessione tecnica, non a una demo lampo.

## Scaletta suggerita per dieci minuti

1. Aprire `examples/bell_ir.json` e il contratto Bell per mostrare i due input.
2. Eseguire la demo Bell e distinguere ampiezze esatte da campioni.
3. Eseguire `duplicate_h` e mostrare la riduzione di profondita da 2 a 0.
4. Aprire certificato e sorgente Lean generati.
5. Compilare il sorgente Lean, gia con toolchain e dipendenze in cache.
6. Chiudere con `lake build` oppure con un test negativo gia predisposto nella
   integration suite.

## Cosa si puo affermare oggi

Il progetto offre attualmente:

- IR JSON validato e versionato per `I`, `X`, `Z`, `H`, `CNOT` e `SWAP`;
- contratti eseguibili con controlli strutturali, di stato, probabilita e
  campionamento;
- esempi fissi verificati per Bell, GHZ(3) e due circuiti Deutsch-Jozsa;
- teorema Lean parametrico per GHZ(n), oltre a unitarieta e preservazione della
  normalizzazione per il linguaggio supportato;
- backend Coq/SQIR per gli esempi fissi e prova di buona formazione del lowering;
- confronto Qiskit dell'operatore completo prima/dopo transpilation;
- certificato Lean o Coq per cancellazioni esatte di porte auto-inverse;
- regressioni tra Qiskit e i due modelli formali, controlli di drift dei file
  generati e casi negativi che devono essere rifiutati.

I limiti da dichiarare sono altrettanto importanti: niente misure, reset,
parametri, controllo classico, rumore o garanzia hardware; il traduttore Python
non e formalmente verificato; i proof assistant controllano il teorema generato,
non l'oggetto Qiskit originale; le prove generate a dimensione fissa scalano
esponenzialmente. La [guida alla presentazione](PRESENTATION_GUIDE.md) e il
[confine di fiducia](TRUST_BOUNDARY.md) contengono la formulazione rigorosa delle
affermazioni.

## Come spiegare il termine contratto

Il file JSON dichiara la specifica: precondizione, postcondizione e controlli
osservabili. Non e, da solo, una prova. `fqv-verify` esegue il circuito ideale e
fornisce evidenza numerica per lo stato iniziale e le tolleranze dichiarate. La
compilazione del teorema Lean o Coq fornisce invece una prova kernel-checked
dell'uguaglianza esatta generata dal contratto.

La lettura in stile Hoare e `{ stato = psi } circuito { stato = phi }`. Per la
corrispondenza Curry-Howard, questa uguaglianza e una proposizione e la prova e
un termine controllato dal kernel. Il progetto non implementa ancora una
Quantum Hoare Logic completa: non usa predicati quantistici generali su matrici
di densita e non tratta misure, rami classici o cicli. Il modello attuale e un
frammento pre/post per stati puri e circuiti unitari finiti.

Per presentare Coq, sottolineare che SQIR significa Small Quantum Intermediate
Representation: e un linguaggio formale tipato per circuiti unitari, dotato di
semantica matriciale completa. Il backend abbassa l'IR condiviso a SQIR, prova
che i circuiti ben formati diventano programmi SQIR ben tipati e usa QuantumLib
per dimostrare le uguaglianze esatte. Non si tratta quindi di una seconda
simulazione numerica.

## Riferimento rapido della CLI

```powershell
fqv-verify --help
fqv-generate --help
```

`fqv-bell` e un alias storico di `fqv-verify`; `fqv-generate-lean` e un alias di
`fqv-generate`. Per una presentazione nuova conviene usare i nomi generali.
Entrambe le CLI terminano con codice `0` in caso di successo; `fqv-verify`
restituisce un codice diverso da zero quando il contratto o l'equivalenza non
passano, caratteristica utile anche in CI.
