# Formal Quantum Validation — Engineering and Research Roadmap

> Documento operativo per l'evoluzione della repository `formal-quantum-validation`.
>
> Obiettivo: trasformare l'attuale prototipo in una piattaforma modulare per la validazione quantistica eseguibile e formale, introducendo progressivamente una struttura software mantenibile, una IR quantistica lineare, contratti sulle risorse e backend formali Lean/Coq.

---

## 1. Visione del progetto

La pipeline target è:

```text
Qiskit circuit
      │
      ▼
Qiskit frontend
      │
      ▼
Raw Quantum IR
      │
      ├── structural validation
      ├── semantic contract validation
      └── linear resource validation
      │
      ▼
Checked Linear IR
      │
      ├── Python executable checker
      ├── Lean proof backend
      ├── Coq/QWIRE backend
      └── Coq/SQIR backend
```

Il centro del progetto non deve essere “dimostrare Bell e GHZ in due prover”, ma definire una **specifica intermedia condivisa** da cui derivare diversi livelli di garanzia:

- validazione strutturale;
- controllo dell'uso lineare dei qubit;
- verifica eseguibile mediante Qiskit;
- dimostrazioni formali in Lean;
- interoperabilità con ambienti Coq specializzati;
- validazione di trasformazioni e ottimizzazioni.

## 1.1 Tesi scientifica

Il progetto non deve presentare il semplice utilizzo congiunto di Qiskit, Lean
e Coq come contributo scientifico. QWIRE possiede già un type system lineare
per circuiti, SQIR/VOQC possiede già una IR e ottimizzazioni verificate, mentre
CoqQ possiede già una logica fondazionale per programmi quantistici.

La tesi scientifica proposta è invece:

> Definire e valutare una IR quantistica lineare e contract-driven che colleghi
> static resource safety, obblighi semantici sullo stato e backend eterogenei
> di validazione, con lowering giustificato formalmente e trusted computing
> base esplicita.

I contributi attesi sono:

1. una IR condivisa con interfacce e lifecycle espliciti;
2. contratti distinti per risorse, stato e osservazioni;
3. un type checker con errori strutturati e certificati verificabili;
4. una prova di soundness del lowering verso la semantica denotazionale;
5. una distinzione formale fra ownership obligation e semantic obligation;
6. una valutazione empirica delle classi di difetti rilevate da ogni livello.

Bell e GHZ restano regressioni e casi didattici. Non devono essere presentati
come il contributo nuovo del lavoro.

## 1.2 Claim e non-claim

Claim previsti:

- la Checked Linear IR esclude specifiche classi di errori di risorsa;
- il lowering preserva interfaccia e denotazione nel frammento supportato;
- ogni rilascio di ancilla produce un obbligo semantico esplicito;
- gli artefatti generati sono deterministici e tracciabili alla sorgente;
- i livelli di garanzia rilevano classi differenti di difetti.

Non-claim obbligatori:

- un controllo numerico Qiskit non è una prova formale;
- due backend che accettano la stessa sorgente non sono automaticamente
  equivalenti;
- il manifest cross-backend prova provenienza comune, non equivalenza;
- linear typing non dimostra che un'ancilla sia separabile o nello stato zero;
- il generatore Python resta trusted finché il suo output o certificato non è
  controllato formalmente.

---

## 2. Stato iniziale da preservare

La repository possiede già:

- circuiti Bell, Bell-minus e GHZ;
- contratti JSON;
- controllo strutturale;
- controllo dello stato finale con `Statevector`;
- controllo di probabilità esatte e campionate;
- IR per `I`, `X`, `Z`, `H`, `CNOT`, `SWAP`;
- validatore della IR;
- confronto numerico sorgente/transpiled;
- generazione di moduli Lean;
- semantica Lean parametrica su `n` qubit;
- prove per Bell, GHZ(3), GHZ(n), unitarietà e normalizzazione;
- test Python e build Lean in CI.

Limiti principali:

1. alcuni moduli hanno troppe responsabilità;
2. Qiskit, dominio, pipeline e backend sono troppo accoppiati;
3. la IR usa indici di qubit ma non modella il lifecycle lineare;
4. ancilla, misura e controllo classico non sono modellati;
5. la CLI è ancora troppo orientata agli esempi;
6. il generatore Lean è testato ma non verificato;
7. la transpilation è controllata numericamente, non certificata;
8. README, versioni e trust boundary devono essere riallineati.

---

# 3. Regole operative per Codex

## 3.1 Modifiche incrementali

- Implementare un milestone alla volta.
- Non introdurre contemporaneamente refactor, Linear IR e Coq.
- Ogni PR deve avere uno scopo unico.
- Non modificare la semantica durante un puro refactor.
- Mantenere compatibilità con i contratti esistenti finché non viene introdotta una nuova versione dello schema.
- Evitare API generiche premature.

## 3.2 Main sempre funzionante

Prima di ogni commit significativo:

```bash
pytest
lake build
```

Quando viene modificato il generatore Lean:

```bash
fqv-generate-lean <ir> <contract> <output>
git diff --exit-code
lake build
```

## 3.3 Nessuna prova incompleta

Non introdurre:

- `sorry`;
- `admit`;
- assiomi ad hoc;
- conversioni non controllate fra indici;
- fallback silenziosi per gate non supportati.

Una costruzione non supportata deve produrre un errore esplicito e tipizzato.

## 3.4 Commit piccoli

Formato consigliato:

```text
refactor(domain): split contract model from parsing
feat(ir): add checked linear wire representation
feat(lean): formalize linear typing judgment
feat(coq): add minimal QWIRE backend
test(ir): reject duplicated quantum resources
docs(architecture): document backend trust boundaries
```

## 3.5 Trust boundary obbligatoria

Ogni componente deve essere classificato come:

- trusted;
- formally verified;
- externally verified;
- executable but unverified;
- test-backed.

---

# 4. Architettura target

```text
src/fqv/
├── domain/
│   ├── amplitudes.py
│   ├── contracts.py
│   ├── expectations.py
│   ├── resources.py
│   └── reports.py
├── ir/
│   ├── schema.py
│   ├── raw.py
│   ├── checked.py
│   ├── operations.py
│   ├── validation.py
│   ├── linear_typing.py
│   ├── lowering.py
│   └── serialization.py
├── frontends/
│   └── qiskit/
│       ├── extraction.py
│       ├── bit_ordering.py
│       └── errors.py
├── backends/
│   ├── python/
│   │   ├── structural.py
│   │   ├── statevector.py
│   │   ├── probabilities.py
│   │   └── transpilation.py
│   ├── lean/
│   │   ├── generator.py
│   │   ├── amplitudes.py
│   │   ├── templates.py
│   │   └── naming.py
│   └── coq/
│       ├── qwire_generator.py
│       ├── sqir_generator.py
│       └── naming.py
├── pipeline/
│   ├── verify.py
│   ├── generate.py
│   ├── transpile.py
│   └── results.py
├── examples/
│   ├── bell.py
│   └── ghz.py
└── cli/
    ├── main.py
    ├── verify.py
    ├── generate_lean.py
    ├── generate_coq.py
    └── transpile.py
```

Struttura Lean suggerita:

```text
lean/QuantumValidation/
├── Semantics/
│   ├── Basis.lean
│   ├── State.lean
│   ├── Gate.lean
│   ├── Circuit.lean
│   └── Measurement.lean
├── Linear/
│   ├── WireType.lean
│   ├── Wire.lean
│   ├── Context.lean
│   ├── Syntax.lean
│   ├── Typing.lean
│   ├── Safety.lean
│   └── Lowering.lean
├── Properties/
│   ├── Unitarity.lean
│   ├── Normalization.lean
│   └── Equivalence.lean
├── Examples/
│   ├── Bell.lean
│   ├── Ghz3.lean
│   └── ParametricGhz.lean
└── Generated/
    ├── Bell.lean
    └── Ghz3.lean
```

---

# 5. Milestone v0.3 — Engineering foundation

## Obiettivo

Riorganizzare il progetto senza modificare il comportamento osservabile.

## 5.1 Baseline di regressione

Prima del refactor:

- registrare tutti i comandi supportati;
- salvare esempi di output testuale e JSON;
- aggiungere test di regressione per Bell, Bell-minus e GHZ;
- documentare l'ordinamento little-endian Qiskit;
- testare gli exit code della CLI.

### Acceptance criteria

- tutti i test esistenti passano;
- gli output pubblici rimangono equivalenti;
- nessuna modifica alla semantica Lean;
- nessuna modifica allo schema dei contratti.

## 5.2 Separare domain model e parsing

Il domain model non deve leggere file, importare Qiskit o eseguire circuiti.

```python
@dataclass(frozen=True)
class QuantumContract:
    name: str
    qubit_count: int
    initial_state: StateSpecification
    target_state: StateSpecification
    resource_expectations: ResourceExpectations
    probability_expectations: tuple[ProbabilityExpectation, ...]
```

Parsing e validazione separati:

```python
def parse_contract_document(document: Mapping[str, object]) -> QuantumContract:
    ...


def validate_contract(
    contract: QuantumContract,
) -> tuple[ContractViolation, ...]:
    ...


def load_contract(path: Path) -> QuantumContract:
    ...
```

### Acceptance criteria

- il domain model non importa Qiskit;
- il domain model non apre file;
- il parser non esegue verifiche quantistiche;
- gli errori sono strutturati;
- i test distinguono parsing failure e semantic validation failure.

## 5.3 Suddividere il checker

```python
class ContractCheck(Protocol):
    def run(
        self,
        circuit: QuantumCircuit,
        contract: QuantumContract,
    ) -> CheckResult:
        ...
```

Implementazioni:

- `StructuralCheck`;
- `ExactStateCheck`;
- `ExactProbabilityCheck`;
- `SampledProbabilityCheck`;
- `TranspilationEquivalenceCheck`.

Composizione:

```python
class VerificationPipeline:
    def __init__(self, checks: Sequence[ContractCheck]) -> None:
        self._checks = tuple(checks)

    def run(
        self,
        circuit: QuantumCircuit,
        contract: QuantumContract,
    ) -> VerificationReport:
        return VerificationReport(
            results=tuple(check.run(circuit, contract) for check in self._checks)
        )
```

### Acceptance criteria

- ogni checker ha test unitari indipendenti;
- un checker può essere disabilitato senza modificarne altri;
- la pipeline orchestra ma non duplica logica;
- `VerificationReport.passed` dipende solo dai risultati.

## 5.4 Isolare la Qiskit frontend

API target:

```python
def extract_raw_ir(circuit: QuantumCircuit) -> RawCircuit:
    ...
```

Il frontend deve rifiutare esplicitamente:

- gate parametrizzati non supportati;
- measurement;
- reset;
- classical control;
- classical operands;
- custom gate opachi;
- arità non supportata.

### Acceptance criteria

- `fqv.ir` non importa Qiskit;
- ogni gate supportato ha un test di extraction;
- ogni costrutto rifiutato ha un test negativo;
- barrier ha una politica documentata;
- bit ordering è centralizzato.

## 5.5 CLI general-purpose

Comandi target:

```text
fqv verify
fqv extract-ir
fqv validate-ir
fqv generate-lean
fqv generate-coq
fqv transpile
```

Esempio:

```bash
fqv verify \
  --example bell \
  --contract contracts/bell.json \
  --emit-ir build/bell.ir.json \
  --report build/bell.report.json
```

### Acceptance criteria

- exit code `0` solo per successo completo;
- output umano su `stdout`;
- diagnostica su `stderr`;
- output JSON stabile e versionato;
- Bell non è hardcoded nel comando principale.

## 5.6 Documentazione e versioning

Aggiornare:

- `pyproject.toml`;
- `lakefile.toml`;
- package version;
- README;
- `docs/DEVELOPMENT.md`;
- `docs/TRUST_BOUNDARY.md`;
- changelog.

Il README deve contenere:

1. obiettivo;
2. architettura;
3. installazione;
4. quick start;
5. esempi;
6. comandi Python;
7. comandi Lean;
8. trust boundary;
9. limitazioni;
10. roadmap.

### Definition of Done v0.3

- struttura modulare;
- test Python verdi;
- build Lean verde;
- nessun cambiamento semantico intenzionale;
- CLI circuit-agnostic;
- README completo;
- versioni allineate;
- nessun modulo con responsabilità eccessivamente eterogenee.

---

# 6. Milestone v0.4 — Linear Quantum IR

## Obiettivo

Rappresentare i qubit come risorse lineari, non come semplici indici globalmente riutilizzabili.

## 6.1 Architecture Decision Record

Creare:

```text
docs/adr/0001-linear-quantum-ir.md
```

La ADR deve decidere:

- identità e versionamento dei wire;
- distinzione quantistico/classico;
- consumo e produzione;
- composizione sequenziale e parallela;
- politica sulle ancilla;
- relazione Raw IR/Checked IR;
- strategia di migrazione JSON.

Decisione consigliata:

> La Raw IR resta semplice e serializzabile. La Checked Linear IR è un oggetto interno costruibile soltanto dopo validazione strutturale e lineare.

La ADR deve inoltre scegliere esplicitamente uno dei seguenti modelli:

1. **Sequential IR con versionamento derivato**: le versioni sono interne e
   servono per analisi e diagnostica;
2. **Quantum SSA / graph IR**: input e output di ogni operazione sono espliciti
   e stale use, fan-out e conflitti paralleli sono rappresentabili;
3. **Calcolo circuitale lineare composizionale**: l'obiettivo principale è
   tipare interfacce, composizione sequenziale e composizione parallela.

La scelta raccomandata per il contributo scientifico è Quantum SSA oppure un
calcolo composizionale. Un semplice contatore di generazioni applicato alla
lista sequenziale attuale rischia di non escludere errori realmente
rappresentabili nella Raw IR.

Prima dell'implementazione, la ADR deve elencare almeno cinque programmi raw
invalidi che il nuovo modello accetta sintatticamente ma rifiuta linearmente.
Se tali esempi non possono essere espressi, il modello di IR è troppo debole.

## 6.2 Tipi di risorsa

```python
class WireKind(Enum):
    QUBIT = "qubit"
    BIT = "bit"


@dataclass(frozen=True, order=True)
class WireId:
    value: str


@dataclass(frozen=True)
class WireVersion:
    wire: WireId
    generation: int
    kind: WireKind
```

Esempio:

```text
q0@0 --H--> q0@1
q0@1, q1@0 --CNOT--> q0@2, q1@1
```

Le versioni precedenti non sono più disponibili.

## 6.3 Raw operations e Checked operations

```python
@dataclass(frozen=True)
class RawOperation:
    gate: str
    operands: tuple[str, ...]
```

```python
@dataclass(frozen=True)
class CheckedH:
    input: WireVersion
    output: WireVersion


@dataclass(frozen=True)
class CheckedCNot:
    control_in: WireVersion
    target_in: WireVersion
    control_out: WireVersion
    target_out: WireVersion
```

La Checked IR non deve poter contenere:

- operandi inesistenti;
- doppio uso dello stesso input;
- output duplicati;
- CNOT con controllo e target uguali;
- riuso di una vecchia versione;
- gate con tipo incompatibile.

## 6.4 Linear type checker Python

```python
@dataclass(frozen=True)
class LinearContext:
    available_quantum: frozenset[WireVersion]
    available_classical: frozenset[WireVersion]


@dataclass(frozen=True)
class LinearTypingResult:
    circuit: CheckedCircuit | None
    final_context: LinearContext | None
    violations: tuple[LinearViolation, ...]

    @property
    def passed(self) -> bool:
        return not self.violations
```

```python
def check_linear_usage(
    raw_circuit: RawCircuit,
    initial_context: LinearContext,
) -> LinearTypingResult:
    ...
```

Algoritmo:

1. inizializzare il contesto;
2. leggere le operazioni in ordine;
3. verificare che gli input siano disponibili;
4. consumare gli input quantistici;
5. produrre nuove versioni;
6. aggiornare il contesto;
7. accumulare errori strutturati;
8. confrontare il contesto finale con il contratto.

## 6.5 Errori tipizzati

```python
class LinearViolationCode(Enum):
    UNKNOWN_WIRE = "unknown_wire"
    STALE_WIRE_VERSION = "stale_wire_version"
    DUPLICATED_INPUT = "duplicated_input"
    INVALID_ARITY = "invalid_arity"
    KIND_MISMATCH = "kind_mismatch"
    IMPLICIT_DISCARD = "implicit_discard"
    DUPLICATED_OUTPUT = "duplicated_output"
    OVERLAPPING_PARALLEL_CONTEXT = "overlapping_parallel_context"
```

Ogni errore deve contenere:

- codice;
- indice operazione;
- gate;
- wire coinvolti;
- messaggio umano;
- dati serializzabili.

## 6.6 Formalizzazione Lean

Non formalizzare subito tutta la logica lineare proposizionale. Introdurre un calcolo mirato.

```lean
inductive WireType
  | qubit
  | bit

structure Wire where
  id : Nat
  generation : Nat
  type : WireType

abbrev LinearContext := Finset Wire
abbrev ClassicalContext := Finset Wire

inductive WellTyped :
    ClassicalContext →
    LinearContext →
    LinearCircuit →
    LinearContext →
    Prop
```

Costruttori iniziali:

- circuito vuoto;
- identity;
- `X`;
- `Z`;
- `H`;
- `CNOT`;
- `SWAP`;
- composizione sequenziale;
- composizione parallela su contesti disgiunti.

## 6.7 Teoremi Lean minimi

```lean
theorem wellTyped_no_quantum_duplication :
  WellTyped Γ Δ circuit Δ' →
  NoQuantumInputDuplicated circuit
```

```lean
theorem wellTyped_no_implicit_discard :
  WellTyped Γ Δ circuit Δ' →
  PreservesRequiredResources Δ circuit Δ'
```

```lean
theorem wellTyped_seq :
  WellTyped Γ Δ₀ c₁ Δ₁ →
  WellTyped Γ Δ₁ c₂ Δ₂ →
  WellTyped Γ Δ₀ (c₁ ++ c₂) Δ₂
```

```lean
theorem wellTyped_parallel_disjoint :
  Disjoint Δ₁ Δ₂ →
  WellTyped Γ Δ₁ c₁ Δ₁' →
  WellTyped Γ Δ₂ c₂ Δ₂' →
  WellTyped Γ (Δ₁ ∪ Δ₂) (parallel c₁ c₂) (Δ₁' ∪ Δ₂')
```

Per il frammento unitario:

```lean
theorem wellTyped_unitary_preserves_qubit_count :
  WellTyped Γ Δ circuit Δ' →
  unitaryFragment circuit →
  quantumCardinality Δ = quantumCardinality Δ'
```

## 6.8 Contratti di risorsa

Schema `0.2` proposto:

```json
{
  "schema_version": "0.2",
  "interface": {
    "inputs": [
      {"name": "q0", "kind": "qubit"},
      {"name": "q1", "kind": "qubit"}
    ],
    "outputs": [
      {"name": "q0_out", "kind": "qubit"},
      {"name": "q1_out", "kind": "qubit"}
    ]
  },
  "resource_policy": {
    "allow_implicit_discard": false,
    "allow_quantum_aliasing": false
  }
}
```

Mantenere compatibilità di lettura con lo schema `0.1` durante la migrazione.

## 6.9 Test richiesti

Positivi:

- `H(q0)`;
- `CNOT(q0, q1)`;
- Bell;
- GHZ(3);
- GHZ(n);
- gate sequenziali con versioni corrette;
- circuiti paralleli su contesti disgiunti.

Negativi:

- uso di `q0@0` dopo aver prodotto `q0@1`;
- `CNOT(q0, q0)`;
- duplicazione dello stesso input;
- output duplicato;
- wire inesistente;
- parallelismo su wire sovrapposti;
- qubit dimenticato;
- bit usato come qubit;
- qubit usato come bit.

### Definition of Done v0.4

- Raw IR e Checked Linear IR separate;
- type checker Python funzionante;
- contratti di risorsa schema `0.2`;
- Bell e GHZ passano il controllo lineare;
- test negativi completi;
- Lean contiene sintassi e typing judgment;
- Lean dimostra almeno no-duplication e composizione sequenziale;
- documentazione della semantica lineare completa.

---

# 6A. Milestone v0.4.5 — Sound lowering e certificati

## Obiettivo

Collegare il type system lineare alla semantica quantistica esistente. Questo
milestone deve essere completato prima di aggiungere backend Coq: senza tale
collegamento, Linear IR e semantica resterebbero due sviluppi paralleli.

## 6A.1 Lowering

Definire una trasformazione totale soltanto sugli input checked:

```python
def lower_checked_circuit(
    circuit: CheckedLinearCircuit,
) -> SemanticCircuit:
    ...
```

Il lowering deve preservare:

- ordine delle operazioni;
- identità logica dei wire;
- interfaccia di input e output;
- gate e operandi;
- convenzione di bit ordering;
- obblighi di lifecycle non ancora scaricati.

## 6A.2 Teorema centrale

Il risultato formale principale deve avere una forma equivalente a:

```lean
theorem lowering_sound :
  WellTyped Γ Δ linearCircuit Δ' →
  denoteLinear linearCircuit =
    denote (lower linearCircuit)
```

Se le due semantiche usano rappresentazioni differenti dei wire, il teorema
deve dichiarare esplicitamente la rinomina o equivalenza di interfaccia.

Corollari minimi:

- no quantum input duplication;
- no implicit discard delle risorse richieste;
- preservazione della cardinalità nel frammento unitario;
- unitarietà del circuito abbassato;
- normalizzazione preservata dal circuito abbassato.

## 6A.3 Certificati

Non è necessario verificare immediatamente l'intero programma Python.
Il type checker Python può produrre:

- Checked Linear IR;
- contesto prima e dopo ogni operazione;
- certificato delle transizioni;
- contesto finale;
- hash del documento sorgente.

Lean deve contenere un checker piccolo e dimostrare:

```lean
theorem accepted_certificate_sound :
  certificateAccepted circuit certificate →
  WellTyped initialContext circuit finalContext
```

Questo riduce la fiducia nel generatore Python più efficacemente di due type
checker indipendenti confrontati soltanto mediante test.

### Definition of Done v0.4.5

- lowering definito soltanto sulla Checked Linear IR;
- preservazione dell'interfaccia dimostrata;
- corrispondenza denotazionale dimostrata;
- formato di certificato versionato;
- certificate checker Lean;
- drift e mutation test sul certificato;
- trust boundary aggiornata.

---

# 7. Milestone v0.5 — Ancilla, uncomputation e lifecycle

## Obiettivo

Rendere esplicito il ciclo di vita delle risorse temporanee.

## 7.1 Nuove operazioni

```text
AllocateZero
AssertZero
Release
```

Evoluzioni successive:

```text
AllocateOne
Measure
Reset
DiscardMeasured
```

## 7.2 Separare ownership e stato

Il type checker lineare può dimostrare:

- che l'ancilla esiste;
- che è usata una sola volta per step;
- che viene restituita o rilasciata.

Non può, da solo, dimostrare che l'ancilla sia tornata in `|0⟩`.

Servono due obblighi:

1. **resource obligation**: l'ancilla non viene persa;
2. **semantic obligation**: è separabile e nello stato richiesto.

Contratto:

```json
{
  "ancillas": [
    {
      "name": "a0",
      "initial_state": "zero",
      "release_condition": "zero",
      "must_be_unentangled": true
    }
  ]
}
```

## 7.3 Primo esempio compute–uncompute

```text
allocate a = |0>
compute f(x) into a
use a as control
uncompute f(x)
assert a = |0>
release a
```

Non descrivere questo passaggio come copia arbitraria di uno stato quantistico.

## 7.4 Teoremi Lean

```lean
theorem released_ancilla_not_in_final_context :
  WellTyped Γ Δ circuit Δ' →
  Releases circuit ancilla →
  ancilla ∉ Δ'
```

```lean
theorem valid_release_requires_zero_obligation :
  WellTyped Γ Δ circuit Δ' →
  ContainsRelease circuit ancilla →
  HasZeroReleaseObligation circuit ancilla
```

La prova dello stato zero può essere:

- generata per circuiti piccoli;
- manuale per esempi parametrici;
- una proof obligation esplicita, mai un'assunzione silenziosa.

## 7.5 Test richiesti

Positivi:

- ancilla allocata, uncomputed e rilasciata;
- più ancilla indipendenti;
- ancilla trasferita fra sottocircuiti.

Negativi:

- release senza allocazione;
- doppio release;
- ancilla dimenticata;
- uso dopo release;
- release senza obbligo semantico;
- alias di un'ancilla.

### Definition of Done v0.5

- lifecycle esplicito;
- contratto di release;
- esempio compute–uncompute;
- test di ownership;
- proof obligation Lean;
- distinzione documentata tra linear safety e semantic correctness.

---

# 8. Milestone v0.6 — Backend Coq/QWIRE

## Obiettivo

Usare QWIRE come backend specializzato per confrontare e validare il modello lineare.

```text
Checked Linear IR
      ├── Lean backend
      └── QWIRE backend
```

## 8.1 Scope iniziale

Supportare solo:

- `I`;
- `X`;
- `Z`;
- `H`;
- `CNOT`;
- `SWAP`, solo se il mapping è pulito;
- Bell;
- GHZ(3).

Non includere subito misura, branching, loop o gate parametrizzati.

## 8.2 Generatore QWIRE

```python
def generate_qwire_module(
    circuit: CheckedCircuit,
    contract: QuantumContract,
    module_name: str,
) -> str:
    ...
```

Separare:

- naming;
- mapping dei gate;
- mapping dei wire;
- template;
- theorem statement;
- proof script.

Feature non supportate devono essere rifiutate prima della generazione.

## 8.3 Domande di ricerca

1. il type checker interno accetta lo stesso frammento di QWIRE?
2. quali errori sono intercettati prima dal frontend?
3. quali proprietà derivano dal solo type checking?
4. quali richiedono la semantica denotazionale?
5. il mapping preserva l'interfaccia delle risorse?

Il confronto con QWIRE è scientificamente più importante della sola
generazione di sintassi QWIRE. Il backend deve quindi documentare:

- quali giudizi sono equivalenti;
- quali programmi sono accettati da un sistema e rifiutati dall'altro;
- come differiscono ownership, ancilla e classical control;
- quali proprietà sono ereditate dal backend e quali dipendono dal traduttore.

## 8.4 Cross-backend manifest

```json
{
  "source_ir_hash": "...",
  "contract_hash": "...",
  "schema_version": "0.2",
  "backends": {
    "lean": {
      "module": "Generated.Bell",
      "status": "verified"
    },
    "coq_qwire": {
      "module": "GeneratedBell",
      "status": "verified"
    }
  }
}
```

Il manifest indica origine comune, non equivalenza automatica fra Lean e Coq.

## 8.5 CI Coq

Job separati:

```text
python-tests
lean-build
coq-qwire-build
generated-artifact-drift
```

Pin delle versioni in file espliciti. Non usare implicitamente “latest”.

## 8.6 Test richiesti

- generazione deterministica;
- Bell compilabile;
- GHZ(3) compilabile;
- circuiti invalidi rifiutati prima del backend;
- feature unsupported con errore chiaro;
- drift check;
- manifest stabile.

### Definition of Done v0.6

- backend QWIRE minimale;
- Bell e GHZ(3) compilano in CI;
- nessuna duplicazione manuale delle specifiche;
- manifest cross-backend;
- trust boundary aggiornata;
- confronto documentato fra il type system interno e QWIRE.

---

# 9. Milestone v0.7 — SQIR/VOQC verified optimization

## Obiettivo

Affiancare alla transpilation numerica Qiskit un percorso di ottimizzazione certificata.

```text
Checked unitary IR
      ├── Qiskit transpiler
      │       └── numerical operator equivalence
      └── SQIR/VOQC
              └── formally verified optimization
```

## 9.1 Scope

Sottoinsieme minimo:

- `X`;
- `H`;
- `CNOT`;
- eventualmente `Rz` solo con parametri esatti;
- composizione sequenziale.

## 9.2 Primo esperimento

Circuito con ridondanze:

```text
H; H
X; X
CNOT; CNOT
```

Obiettivi:

- Qiskit lo semplifica;
- SQIR/VOQC lo semplifica;
- Python confronta gate count e depth;
- VOQC fornisce la garanzia formale nel proprio modello;
- il report distingue prova formale e controllo numerico.

## 9.3 Report comparativo

```json
{
  "source": {
    "gate_count": 8,
    "depth": 6
  },
  "qiskit": {
    "gate_count": 3,
    "depth": 3,
    "equivalence": "numerically_checked"
  },
  "voqc": {
    "gate_count": 3,
    "depth": 3,
    "equivalence": "formally_verified_in_coq"
  }
}
```

Non dichiarare che il risultato Qiskit sia formalmente verificato.

## 9.4 Trust boundary

Documentare separatamente:

- correttezza di VOQC nel modello SQIR;
- correttezza del traduttore IR→SQIR;
- correttezza di SQIR→Qiskit/OpenQASM;
- affidabilità delle metriche;
- equivalenza delle convenzioni di bit ordering.

### Definition of Done v0.7

- esperimento riproducibile;
- generatore SQIR minimale;
- ottimizzazione Coq in CI;
- report Qiskit-vs-VOQC;
- trust boundary dettagliata;
- nessuna affermazione più forte delle garanzie reali.

---

# 10. Milestone v0.8 — Misura, controllo classico e CoqQ

## Obiettivo

Passare dal frammento unitario a programmi quantistici con effetti.

Questa fase inizia solo dopo la stabilizzazione della Linear IR e del lifecycle delle ancilla.

## 10.1 Estensioni della IR

```text
Measure
Reset
ClassicalIf
Sequence
Parallel
```

```python
@dataclass(frozen=True)
class CheckedMeasure:
    qubit_in: WireVersion
    qubit_out: WireVersion
    bit_out: WireVersion
```

La misura:

- consuma una versione del qubit;
- produce una versione post-misura;
- produce un bit classico duplicabile.

## 10.2 Semantica

La semantica di stato puro non basta. Introdurre gradualmente:

- matrici densità;
- superoperatori;
- distribuzioni sugli esiti;
- trace parziale;
- canali quantistici;
- branching classico.

Non implementare tutto in una singola PR.

## 10.3 CoqQ

Usare CoqQ per:

- quantum-while programs;
- quantum Hoare logic;
- frame rules;
- disgiunzione dei registri;
- specifiche di protocolli.

Primi casi d'uso:

- teleportation;
- superdense coding;
- protocollo con misura e correzione condizionale.

### Definition of Done v0.8

- misura tipata linearmente;
- bit classici distinti dai qubit;
- almeno un protocollo;
- semantica non unitaria esplicita;
- primo contratto Hoare;
- integrazione CoqQ documentata.

---

# 11. Strategia Lean vs Coq

## Lean rimane il core

Usare Lean per:

- definizione originale della Linear IR;
- proprietà del type checker;
- corrispondenza Checked IR/semantica;
- contratti di risorsa;
- teoremi parametrici;
- proprietà specifiche della pipeline.

## Coq come ecosistema specializzato

Usare:

- QWIRE per linear typing;
- SQIR/VOQC per verified compilation;
- CoqQ per quantum program logic e misura.

## Regola fondamentale

Non implementare:

```text
Qiskit → Lean → Coq
```

Implementare:

```text
                ┌── Lean
Shared IR ──────┼── QWIRE
                ├── SQIR/VOQC
                └── Python/Qiskit
```

---

# 12. Ordine delle issue

## Epic A — Engineering

- [ ] A1 — Add regression baseline
- [ ] A2 — Split contract domain model from JSON parsing
- [ ] A3 — Split executable checks
- [ ] A4 — Isolate Qiskit frontend
- [ ] A5 — Reorganize Lean generator
- [ ] A6 — Introduce circuit-agnostic CLI
- [ ] A7 — Align versions and documentation
- [ ] A8 — Update trust boundary
- [ ] A9 — Add generated artifact drift checks

## Epic B — Linear IR

- [ ] B1 — Write ADR for linear resources
- [ ] B2 — Add wire identity and versioning
- [ ] B3 — Split Raw IR and Checked IR
- [ ] B4 — Implement linear context
- [ ] B5 — Implement type checker
- [ ] B6 — Add structured violations
- [ ] B7 — Add resource contracts
- [ ] B8 — Migrate Bell and GHZ
- [ ] B9 — Add negative resource tests

## Epic C — Lean

- [ ] C1 — Define wire types
- [ ] C2 — Define linear/classical contexts
- [ ] C3 — Define linear circuit syntax
- [ ] C4 — Define typing judgment
- [ ] C5 — Prove sequential composition
- [ ] C6 — Prove no duplication
- [ ] C7 — Prove qubit-count preservation
- [ ] C8 — Connect syntax to current denotation
- [ ] C9 — Prove Bell and GHZ well-typed

## Epic D — Ancilla

- [ ] D1 — Add allocation
- [ ] D2 — Add zero assertion
- [ ] D3 — Add release
- [ ] D4 — Add lifecycle checker
- [ ] D5 — Add semantic release obligation
- [ ] D6 — Implement compute–uncompute example
- [ ] D7 — Add Lean lifecycle properties

## Epic E — QWIRE

- [ ] E1 — Pin Coq/QWIRE toolchain
- [ ] E2 — Add QWIRE generator skeleton
- [ ] E3 — Generate Bell
- [ ] E4 — Generate GHZ(3)
- [ ] E5 — Add Coq CI
- [ ] E6 — Add cross-backend manifest
- [ ] E7 — Document semantic differences

## Epic F — SQIR/VOQC

- [ ] F1 — Define supported shared subset
- [ ] F2 — Add SQIR generator
- [ ] F3 — Add redundant circuit benchmark
- [ ] F4 — Run verified optimization
- [ ] F5 — Compare with Qiskit transpiler
- [ ] F6 — Produce structured report
- [ ] F7 — Document translation trust boundary

---

# 13. Template per issue Codex

```markdown
## Goal

Descrivere un solo risultato osservabile.

## Context

Indicare i moduli coinvolti e i vincoli architetturali.

## Required changes

- file da creare;
- file da modificare;
- API da introdurre;
- comportamento da preservare.

## Non-goals

Elencare ciò che non deve essere implementato.

## Tests

Elencare test positivi, negativi e di regressione.

## Acceptance criteria

Condizioni verificabili e binarie.

## Validation commands

```bash
pytest
lake build
```

## Trust-boundary impact

Indicare se il componente è trusted, test-backed o formally verified.
```

---

# 14. Prima issue raccomandata

## Titolo

```text
refactor(domain): separate contract model, parsing and validation
```

## Goal

Separare le classi di dominio dei contratti dalla lettura JSON e dalla validazione.

## Required changes

1. creare `src/fqv/domain/`;
2. spostare le dataclass pure in `domain/contracts.py`;
3. spostare le aspettative in `domain/expectations.py`;
4. creare `domain/parsing.py`;
5. creare errori strutturati;
6. mantenere wrapper temporanei per le API esistenti;
7. aggiornare import e test;
8. non modificare lo schema JSON;
9. non modificare la semantica dei checker.

## Non-goals

- Linear IR;
- Coq;
- modifica della CLI;
- modifica dei circuiti;
- modifica dei teoremi Lean.

## Acceptance criteria

- il domain model non importa Qiskit;
- il domain model non apre file;
- il parser restituisce domain objects;
- la validazione è separata;
- tutti i test esistenti passano;
- nuovi test distinguono documento malformato, schema invalido e contratto semanticamente invalido.

---

# 15. Metriche

Per ogni milestone registrare:

- moduli con dipendenza diretta da Qiskit;
- dimensione dei principali file Python;
- copertura dei test;
- gate supportati da Raw IR e Checked IR;
- numero di backend;
- teoremi senza `sorry`;
- artefatti generati deterministicamente;
- componenti trusted;
- componenti formalmente verificati;
- esempi end-to-end.

Non usare il solo numero di linee come metrica di qualità.

---

# 16. Rischi e mitigazioni

## Duplicazione Lean/Coq

- specifica condivisa;
- generatori separati;
- niente riscrittura manuale degli esempi;
- manifest con hash della sorgente.

## Type system troppo ambizioso

- iniziare con un calcolo minimo;
- non formalizzare tutta la logica lineare;
- aggiungere measurement dopo il frammento unitario;
- separare ownership e correttezza semantica.

## IR troppo legata a Qiskit

- nessun import Qiskit nel core;
- bit ordering confinato nel frontend;
- gate naming indipendente dal provider;
- schema versionato.

## Affermazioni eccessive

Distinguere sempre:

- numerically checked;
- type checked;
- generated and kernel checked;
- formally verified;
- translation test-backed.

## Più toolchain

- pin delle versioni;
- job CI separati;
- backend opzionali;
- Coq solo dopo v0.4.

---

# 17. Risultato scientifico atteso

Il progetto potrà essere descritto come:

> Una piattaforma interoperabile per la validazione quantistica basata su una IR lineare condivisa, capace di combinare controlli eseguibili, contratti di risorsa, prove Lean, linear typing QWIRE e ottimizzazioni certificate SQIR/VOQC.

Domande di ricerca:

1. quali errori possono essere esclusi staticamente dalla Linear IR?
2. quali proprietà richiedono una dimostrazione semantica?
3. come separare lifecycle dei qubit e stato quantistico?
4. come confrontare backend formali senza assumere equivalenza automatica?
5. quale parte della pipeline rimane trusted?
6. quali trasformazioni possono essere certificate end-to-end?
7. come combinare contratti di risorsa, stato e osservazione?

## 17.1 Piano di valutazione

Un paper richiede una valutazione, non soltanto esempi positivi. Preparare un
corpus con circuiti corretti e mutazioni controllate.

Classi minime di mutazione:

- wire inesistente;
- versione stale;
- duplicazione o aliasing;
- operando fuori range;
- fase relativa errata;
- gate mancante o extra;
- ordine invertito;
- errore di bit ordering;
- ancilla non uncomputed;
- release prematuro;
- release di ancilla entangled;
- trasformazione non equivalente.

Per ogni mutazione registrare quale livello la intercetta:

```text
structural validation
linear typing
statevector check
operator equivalence
Lean semantic proof
certificate checker
specialized backend
```

Metriche sperimentali:

- detection rate per classe di difetto;
- falsi positivi e falsi negativi;
- tempo di parsing, typing, lowering e checking;
- dimensione dei certificati;
- crescita rispetto a qubit e operazioni;
- componenti rimasti trusted;
- concordanza e divergenza fra backend.

Benchmark minimi:

- Bell e GHZ come regressioni;
- circuiti modulari sequenziali e paralleli;
- compute–uncompute con ancilla;
- almeno un algoritmo con input parametrico;
- almeno un protocollo con misura nella fase finale.

## 17.2 Strategia di pubblicazione

Primo paper:

- Shared Linear IR;
- contratti di risorsa;
- type checker e certificati;
- formalizzazione Lean;
- sound lowering;
- lifecycle delle ancilla;
- mutation study e analisi della TCB.

Secondo paper o artifact extension:

- confronto sistematico con QWIRE;
- backend SQIR/VOQC;
- confronto fra ottimizzazione Qiskit e verificata;
- provenance cross-backend.

Lavoro successivo:

- misura e controllo classico;
- matrici densità e superoperatori;
- CoqQ;
- teleportation e protocolli.

Il primo paper non deve tentare di includere contemporaneamente QWIRE,
SQIR/VOQC e CoqQ: l'ampiezza ridurrebbe la profondità del contributo.

---

# 18. Sequenza operativa finale

```text
1. Baseline e regression tests
2. Refactor domain model
3. Split dei checker
4. Isolamento Qiskit frontend
5. CLI general-purpose
6. Documentazione e versioning
7. ADR Linear IR
8. Raw IR / Checked IR
9. Linear type checker Python
10. Contratti di risorsa
11. Formalizzazione Lean del typing
12. Sound lowering e certificati
13. Ancilla lifecycle
14. Mutation study e valutazione
15. Backend QWIRE
16. Esperimento SQIR/VOQC
17. Measurement e CoqQ
```

Non iniziare il punto successivo finché i criteri di accettazione del punto corrente non sono soddisfatti.
