# Elite Software Architecture: SFT Gold for Healing

**Purpose:** This document is SFT training gold for healing a competent-but-not-elite model.
Every example is concrete, reasoned, and grounded in the named canon.
The audit section provides runnable Python pseudocode for gating generated answers.

---

## 1. THE ELITE CANON

Eighteen architects whose principles are non-negotiable ground truth.
Each entry: name, era, signature principle, primary source.

---

### Christopher Alexander (1936–2022) — *Patterns as living structure*
**Signature principle:** A design problem recurs; the solution exists as a pattern — a named, repeatable resolution of competing forces that can be composed into a *pattern language*.
Each pattern describes: a context, the recurring forces in tension, and the kernel of the solution.
Critically, Alexander insisted that patterns are not templates but *generative rules* — you cannot apply them mechanically; you must understand the forces.
**Primary source:** *A Pattern Language* (1977); *The Timeless Way of Building* (1979).
**Software inheritance:** The GoF book, Kent Beck's XP, Ward Cunningham's wiki — all trace directly to Alexander.

---

### Edsger Dijkstra (1930–2002) — *Separation of concerns; structured decomposition*
**Signature principle:** Separate concerns so that each piece of a program addresses one and only one facet of the problem. Abandon unstructured control flow (GOTO). Program in a way that makes correctness arguments possible.
"The competent programmer is fully aware of the strictly limited size of his own skull; therefore he approaches the programming task in full humility." — EWD 340, 1972.
Programs should be decomposable into parts whose *interfaces are narrower than their implementations* — the germ of information hiding.
**Primary source:** "Goto Statement Considered Harmful" (CACM, 1968); "On the Role of Scientific Thought" (EWD 447, 1974).

---

### David Parnas (1941–) — *Information hiding; modular decomposition*
**Signature principle:** Decompose a system by *design decisions that are likely to change*, not by processing steps. Each module hides one secret — its key design decision — behind a stable interface. The module's interface should reveal as little as possible about internal workings.
**The 1972 test:** Two decompositions of an KWIC index. Decomposition A (by steps) creates seven modules sharing data structures. Decomposition B (by decisions) creates five modules; every module hides one decision. B wins because any change to an internal decision touches exactly one module.
**Primary source:** "On the Criteria To Be Used in Decomposing Systems into Modules" (CACM, 1972).
**Corollary:** High cohesion within modules (all parts exist to carry out the hidden secret), low coupling between modules (communicate only through stable interfaces).

---

### Barbara Liskov (1939–) — *Substitutability; abstract data types*
**Signature principle (LSP):** If S is a subtype of T, then objects of type T may be replaced by objects of type S without altering any of the desirable properties of the program. Inheritance is a *behavioral contract*, not merely code reuse.
Liskov introduced abstract data types (CLU, 1974): the representation is hidden; only the operations are visible. This is information hiding instantiated in type theory.
**The design test:** If you find yourself checking `isinstance` before calling a method, or overriding a method to raise `NotImplementedError`, you have violated LSP — rethink the hierarchy or use composition.
**Primary source:** "Data Abstraction and Hierarchy" (OOPSLA Keynote, 1987); "A Behavioral Notion of Subtyping" with Wing (1994).

---

### Fred Brooks (1931–2022) — *Essential vs. accidental complexity*
**Signature principle:** Software complexity has two parts. *Essential complexity* is inherent in the problem domain — it cannot be removed. *Accidental complexity* is the friction we add via tools, languages, process, architecture — it can and must be removed. No single technique yields an order-of-magnitude improvement because essential complexity dominates.
**The architectural implication:** Every layer, every abstraction, every framework you add must reduce more accidental complexity than it introduces. If it doesn't, remove it. The simplest architecture that correctly captures the essential complexity is the best one.
**Primary source:** "No Silver Bullet" (IFIPS, 1986); *The Mythical Man-Month* (1975).

---

### Melvin Conway (1937–) — *Organizational mirroring*
**Signature principle (Conway's Law):** "Organizations which design systems are constrained to produce designs which are copies of the communication structures of those organizations." (1967)
**Reverse Conway maneuver:** The architectural implication is bidirectional. If you want a certain architecture, deliberately organize teams to mirror it. If your teams are siloed, your interfaces will be silo boundaries whether you intend them or not.
**The design test:** When you draw the module/service boundary map, overlay it with the team org chart. If they differ substantially, one will deform the other — and it won't be the org chart.
**Primary source:** "How Do Committees Invent?" (Datamation, 1968).

---

### Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides (GoF, 1994) — *Compositional patterns; program to interfaces*
**Signature principles:**
1. *Program to an interface, not an implementation.* Dependencies should point at abstractions, never at concrete classes.
2. *Favor object composition over class inheritance.* Inheritance is a static, compile-time coupling. Composition is dynamic and can vary at runtime.
**The 23 patterns** are a vocabulary, not a checklist. Their deeper contribution is that recurring design problems can be named, and named solutions can be communicated, composed, and critiqued.
**Caution:** Patterns are not free — each introduces indirection, vocabulary cost, and conceptual overhead. Apply only when the forces they balance actually exist in your problem.
**Primary source:** *Design Patterns: Elements of Reusable Object-Oriented Software* (1994).

---

### Robert C. Martin (Uncle Bob, 1952–) — *SOLID; the Dependency Rule; Clean Architecture*
**Signature principle (The Dependency Rule):** In a layered, concentric-ring architecture, *source code dependencies can only point inward*. Outer rings (frameworks, UI, DB) depend on inner rings. Inner rings (entities, use cases) know nothing about outer rings. The domain model must have zero imports from frameworks, ORMs, or HTTP libraries.
**SOLID condensed:**
- S: Each module has one reason to change (one actor it serves).
- O: Open for extension, closed to modification — extend via new code, not by editing existing code.
- L: LSP — substitutability (Liskov).
- I: Interfaces should be narrow and client-specific, not fat and general.
- D: Depend on abstractions; high-level policy must not depend on low-level detail.
**Primary source:** *Clean Architecture* (2017); "Clean Architecture" blog post (2012).

---

### Alistair Cockburn (1953–) — *Hexagonal architecture; ports and adapters*
**Signature principle:** An application should be equally driveable by humans, automated tests, other programs, or batch scripts. Achieve this by surrounding the core with *ports* (purpose-defined interfaces) and *adapters* (technology-specific implementations of those ports).
**Structure:**
- **Left/driving side (primary ports):** How the outside world tells the application to do something. A REST controller is an adapter for the HTTP port. A CLI runner is an adapter for the command port.
- **Right/driven side (secondary ports):** How the application tells infrastructure to do something. A `UserRepository` interface is a port; its PostgreSQL implementation is an adapter.
**The crucial test:** You must be able to swap any adapter — replace PostgreSQL with SQLite, replace REST with CLI, replace email with a fake — without touching the application core.
**Primary source:** "Hexagonal Architecture" (alistair.cockburn.us, 2005; conceived 1994).

---

### Roy Fielding (1965–) — *REST; architectural constraints as design*
**Signature principle:** REST is not HTTP + JSON. It is a set of *architectural constraints* that, when applied, yield specific properties:
1. **Stateless:** Each request carries all context. No server-side session. Enables horizontal scale.
2. **Uniform interface:** Resources are named by URI. Representations (JSON, HTML) are separate from the resource. HTTP verbs carry semantic meaning. Responses carry their own discoverability (HATEOAS at full maturity).
3. **Layered system:** Clients cannot tell whether they are connected to a server or a cache or a gateway.
4. **Client–server separation:** UI concerns and data-storage concerns evolve independently.
**The implication:** A REST API that uses sessions, or whose URLs encode verbs (`/createOrder`), or whose clients require out-of-band documentation to navigate, is not REST — it is RPC over HTTP. The distinction matters because Fielding's constraints exist to give you specific *scalability and evolvability* properties, not aesthetics.
**Primary source:** Roy Fielding, doctoral dissertation, Chapter 5 (UC Irvine, 2000).

---

### Eric Evans (1959–) — *Domain-Driven Design; bounded contexts; ubiquitous language*
**Signature principles:**
1. **Ubiquitous language:** A single, shared vocabulary — negotiated between domain experts and developers — that is used in code, tests, conversation, and documentation without translation.
2. **Bounded context:** A linguistic and logical boundary inside which a particular model applies consistently. Outside the boundary, the same word may mean something different. Never share a model across contexts — share explicit integration contracts instead.
3. **Aggregate:** A cluster of domain objects with a single root entity that enforces invariants. External code may only reference the aggregate root; internal members are private.
4. **Domain vs. infrastructure:** Domain logic belongs in entities, value objects, and domain services. Infrastructure (persistence, messaging) belongs outside the domain layer.
**The design test:** If a domain entity imports a repository, or if a service method touches more than one aggregate in a single transaction, the design is wrong.
**Primary source:** *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003).

---

### Martin Fowler (1963–) — *Refactoring; patterns of enterprise architecture; evolutionary architecture*
**Signature principles:**
1. **Refactoring is continuous design:** Code rots under change. Refactoring (behavior-preserving restructuring, under test) is the mechanism that keeps design honest over time. Without it, every feature degrades the structure.
2. **Strangler Fig:** Migrate a monolith to a new architecture by building the new system around the old one, routing traffic incrementally, until the old system can be removed. Never attempt a big-bang rewrite.
3. **Branch by abstraction:** To replace a module, first introduce an abstraction layer, migrate callers to the abstraction, then swap implementations — all while the system ships.
**Primary source:** *Refactoring* (1999, 2018); *Patterns of Enterprise Application Architecture* (2002); martinfowler.com.

---

### Kent Beck (1961–) — *Simple design; TDD; XP*
**Signature principle (Four Rules of Simple Design, priority order):**
1. Passes all tests.
2. Reveals intention (code reads as what it means, not how it works).
3. No duplication (DRY — but also no hidden conceptual duplication).
4. Fewest elements (no speculative abstraction; YAGNI).
**TDD loop:** Red (write a failing test that specifies behavior) → Green (write the minimum code to pass) → Refactor (improve design without changing behavior). The tests become the specification and the safety net simultaneously.
**Primary source:** *Extreme Programming Explained* (1999); *Test-Driven Development: By Example* (2002).

---

### Gregor Hohpe (1971–) — *Enterprise Integration Patterns; messaging architecture*
**Signature principles:**
1. Integration systems must be designed around *messaging patterns*, not point-to-point RPCs. The 65 EIP patterns (pipes and filters, pub/sub, content-based routing, aggregator, scatter-gather) are the vocabulary.
2. Prefer *choreography over orchestration* for loose coupling: each service reacts to events independently rather than being commanded by a central orchestrator that accrues coupling.
3. The *Dead Letter Channel* and idempotent receivers are not optional extras — they are the difference between a distributed system and a fragile one.
**Primary source:** *Enterprise Integration Patterns* (with Bobby Woolf, 2003).

---

### Sam Newman (1979–) — *Microservices; service boundaries; independent deployability*
**Signature principles:**
1. Service boundaries should follow *business domain boundaries* (DDD bounded contexts), not technical layers. A "service per layer" (UserController service, UserDB service) is not a microservice architecture — it is a distributed monolith.
2. **Independent deployability** is the north star. If deploying Service A requires coordinating with Service B, the boundary is wrong.
3. **Prefer monolith first.** Getting service boundaries wrong is expensive. Start monolithic until you know your domain well enough to cut the right boundaries.
4. Coupling is multidimensional: domain coupling, temporal coupling, technology coupling. Minimize all three across service boundaries.
**Primary source:** *Building Microservices* (2nd ed., 2021).

---

### Leslie Lamport (1941–) — *Distributed systems; logical time; consensus*
**Signature principles:**
1. **Logical clocks:** Physical clocks cannot reliably order events in a distributed system. Lamport clocks assign logical timestamps that respect the *happened-before* relation. Vector clocks extend this to capture causality.
2. **Paxos / consensus:** Distributed agreement is hard. A consensus algorithm (Paxos, Raft) is the correct tool for replicating state. Ad-hoc locking and two-phase commit without careful thought about failures will produce split-brain, corruption, or livelock.
3. **TLA+ / specification:** Write a formal specification of the system's invariants before implementation. Many distributed system bugs are *design* bugs, not code bugs.
**Primary source:** "Time, Clocks, and the Ordering of Events in a Distributed System" (CACM, 1978); "The Part-Time Parliament" (1998); *Specifying Systems* (2002).

---

### Rich Hickey (1960–) — *Simplicity vs. ease; data orientation; immutable values*
**Signature principles:**
1. **Simple ≠ easy.** *Simple* means not intertwined, not braided together. *Easy* means familiar or nearby. Conflating them is the source of most architectural complexity.
2. **Pull state, identity, and behavior apart.** Object-oriented conflation of these three things into a single stateful object is a primary source of incidental complexity.
3. **Prefer data.** Plain, immutable data (maps, lists, values) is the most composable, testable, loggable form of information. Functions over data compose naturally; method hierarchies do not.
4. **Avoid place-oriented programming.** When state lives in mutable places, reasoning about time (what was the value *when*?) becomes impossible.
**Primary source:** "Simple Made Easy" (Strange Loop keynote, 2011).

---

### Joe Armstrong (1950–2019) — *Actor model; fault tolerance; let it crash*
**Signature principles:**
1. **Share nothing.** Processes communicate only by message passing; no shared mutable state. This is the only safe concurrency primitive at scale.
2. **Let it crash.** Don't write defensive code that tries to handle every possible failure in-place. Instead, structure the system into a *supervision tree*. When a process fails, its supervisor restarts it. Failure is explicit and localized; the crash is the error signal.
3. **Supervision hierarchies are architecture.** The tree of supervisors — and their restart strategies (one-for-one, one-for-all, rest-for-one) — IS the fault-tolerance design. It must be as deliberate as the module structure.
**Primary source:** *Programming Erlang* (2007); Joe Armstrong's doctoral thesis (2003).

---

### Pat Helland (1957–) — *Data inside vs. outside; immutable outside data*
**Signature principles:**
1. **Data inside a service is mutable and owned.** Data that crosses a service boundary becomes *immutable* — a snapshot at a point in time, with a version/identifier. Never share mutable state across trust boundaries.
2. **Outside data must be self-describing.** A message sent between services must carry its schema and version. Receivers must be able to parse future messages without breakage (additive evolution only).
3. **Identifiers are the skeleton of integration.** Distributed collaborations are woven together by stable identifiers (order-id, customer-id). The same entity may have different representations in different services, unified only by identifier.
**Primary source:** "Data on the Outside versus Data on the Inside" (CIDR, 2005); "Immutability Changes Everything" (CIDR, 2015).

---

### Michael Feathers (1966–) — *Working with legacy code; seams; dependency breaking*
**Signature principles:**
1. **Legacy code is code without tests.** Age is not the criterion.
2. **A seam is a place where you can change behavior without editing that place** — a virtual method, a dependency injection point, a configurable factory. Finding and creating seams is the prerequisite to testing.
3. **The Golden Rule of Legacy Change:** Understand, then test, then change. Never change untested code "just to see what happens."
**Primary source:** *Working Effectively with Legacy Code* (2004).

---

## 2. CHECKABLE ELITENESS CRITERIA

These are the architectural laws. An answer that violates any of them is not elite, regardless of how fluent it sounds.

---

### C1. High Cohesion / Low Coupling (Parnas, 1972)
**What it means:** Within a module, every element exists to carry out a single, well-defined secret. Between modules, the only contact is through narrow, stable interfaces.
**Checkable tells:**
- A module has a single noun name that captures its purpose (not `Utils`, `Manager`, `Helper`).
- Removing one class/function from the module makes the rest meaningless — they are all needed together.
- The module has few imports from *other* application modules; most imports are from the stdlib or declared dependencies.
- Change a module's implementation without touching its interface; no other module requires recompilation.
**Failure modes:** God class, `Utils.py`, `ServiceHelper`, modules named after layering rather than concept.

---

### C2. Information Hiding (Parnas, 1972)
**What it means:** Every module hides one design decision — the decision most likely to change — behind a stable interface.
**Checkable tells:**
- Can you change the database from PostgreSQL to SQLite, or the serialization from JSON to protobuf, or the cache from Redis to in-memory, by touching exactly one module?
- Does the interface use domain vocabulary, not infrastructure vocabulary? (`UserRepository.find_by_email()` not `UserPGAdapter.execute_select()`)
**Failure modes:** Leaking `Session`, `Connection`, `Row`, `PreparedStatement` objects through the interface; returning framework types from domain methods.

---

### C3. The Dependency Rule (Martin, 2012)
**What it means:** In a layered/concentric architecture, every source code `import` points inward (toward greater abstraction, toward the domain). The innermost ring (entities/domain) has zero knowledge of frameworks, databases, or HTTP.
**Checkable tells:**
- No `import django`, `import sqlalchemy`, `import flask` anywhere inside the domain package.
- Repository interfaces are declared in the domain or application layer; their implementations live in infrastructure.
- Use cases accept and return domain objects, not request/response DTOs from the framework.
**Failure modes:** Domain entities with `@Column`, `@Entity`, `@JsonProperty`; use cases that call `request.json` or `response.status_code`.

---

### C4. Separation of Concerns (Dijkstra, 1974; Evans, 2003)
**What it means:** Each distinct concern (business rule, persistence, presentation, messaging, validation, authentication) is handled in exactly one place, and the places are organized into layers/slices that do not bleed into each other.
**Checkable tells:**
- SQL does not appear in a controller.
- Rendering logic does not appear in a service.
- Authentication does not appear inside a domain aggregate.
- A domain object that validates itself does so in terms of *domain invariants*, not HTTP status codes.
**Failure modes:** Fat controllers, smart repositories that contain business logic, domain objects that call `send_email()`.

---

### C5. Ports and Adapters / Hexagonal (Cockburn, 2005)
**What it means:** The application core is surrounded by ports (interfaces defining purpose) and adapters (concrete implementations). You can drive the core from a test with no infrastructure.
**Checkable tells:**
- The test suite can run with no database, no network, no filesystem by substituting in-memory adapters.
- A new delivery mechanism (CLI, gRPC, message consumer) can be added without touching the application core.
- A new secondary adapter (swap PostgreSQL for DynamoDB) requires only implementing one interface.
**Failure modes:** Tests that require a running database; service methods that instantiate `psycopg2.connect()` directly; controllers that contain business logic.

---

### C6. Composition Over Inheritance (GoF, 1994)
**What it means:** Prefer assembling behavior from collaborating objects over extending via inheritance. Inheritance is a static, compile-time coupling; composition is dynamic and replaceable.
**Checkable tells:**
- Inheritance hierarchies deeper than 2 levels are a warning sign.
- "Behavior variation" is achieved by injecting a strategy/policy object, not by subclassing and overriding.
- The base class has no concrete methods that subclasses "accidentally" inherit — that is the fragile base class problem.
**Failure modes:** Abstract base classes with 10+ methods; subclasses that override methods to do nothing or raise `NotImplementedError`; "mixin" chains where behavior is impossible to trace.

---

### C7. Conway's Law Awareness (Conway, 1968)
**What it means:** Service and module boundaries should align with team boundaries. Alternatively, use the Reverse Conway Maneuver: reorganize teams to mirror the target architecture.
**Checkable tells:**
- Each service/bounded context is owned by one team. Two teams never share ownership of one module.
- The APIs between services match the communication channels between teams.
**Failure modes:** A single "shared" module owned by everyone (no one); services whose boundaries cut across team lines, requiring constant coordination to ship.

---

### C8. Make the Right Thing Easy; Make the Wrong Thing Hard (Rico Mariani; Beck, 1999)
**What it means:** API surfaces and module boundaries should be designed so that correct usage requires no discipline or documentation. Incorrect usage should be a compile error, a type error, or at minimum an obvious mistake.
**Checkable tells:**
- A type system enforces domain invariants (use `CustomerId` not `str`; use `NonEmptyList` not `List`).
- Constructors/factory methods validate preconditions; invalid objects cannot exist.
- Interfaces that encourage mutation are replaced with builders or functional pipelines.
**Failure modes:** `id: str` for all identifiers (allows passing a product id where an order id is required); mutable default arguments; constructors that accept `None` silently.

---

### C9. The Structure IS the Design (Alexander, 1977; Evans, 2003)
**What it means:** The directory/package structure of the codebase must reflect the domain model and architectural intent, not historical accident. A new engineer should be able to infer the architecture from the file tree.
**Checkable tells:**
- Top-level packages are bounded contexts or domain areas, not `controllers/`, `services/`, `models/` (technical layering).
- Within a bounded context, the internal layering follows the dependency rule (domain is the deepest, infrastructure is the outermost).
- Module names use ubiquitous language, not technical vocabulary.
**Failure modes:** A flat `models.py` with 50 classes; a `helpers/` directory that acts as a dumping ground; package names that encode the implementation technology.

---

## 3. FIVE COMPLETE GOLD EXAMPLES

Each example is: a prompt, the elite answer with full reasoning, and the criteria it satisfies.

---

### Gold 1 — Module Design: KWIC Index (Parnas's Classic, Correctly Solved)

**PROMPT:**
> Design a modular breakdown for a KWIC (Keyword In Context) index system.
> The system reads lines of text, produces all circular shifts of each line,
> sorts them alphabetically, and outputs the sorted shifts.
> Show a module decomposition and explain your criterion for decomposition.

**ELITE ANSWER:**

The wrong decomposition (Parnas's "Decomposition 1") cuts by processing stages: Input, Circular Shift, Alphabetizer, Output, Master Control. These five modules share data structures — they all reference the same in-memory representation of lines and shifts. Change the representation from an array of strings to an array of indices and every module must change.

The right decomposition cuts by **design decisions that are likely to change**:

```
Module: LineStorage
  Secret: How lines are stored in memory (array? linked list? memory-mapped file?)
  Interface: store(line: str), get(n: int) -> str, count() -> int

Module: CircularShifter
  Secret: How circular shifts are enumerated and stored
  Interface: setup(), shift_count() -> int, get_shift(i: int) -> str

Module: Alphabetizer
  Secret: The sorting algorithm and its data representation
  Interface: alpha_setup(), ith_alphabetized(i: int) -> str

Module: Output
  Secret: How results are rendered (stdout, file, HTML)
  Interface: print_all()

Module: MasterControl
  Secret: Sequencing — the order in which other modules are called
  Interface: run()
```

**Why this wins:**

1. `LineStorage` hides the representation. If you switch from storing full strings to storing line indices to save memory, only `LineStorage` changes. `CircularShifter` never knew the representation; it only called `LineStorage.get()`.

2. `CircularShifter` hides how shifts are generated (compute-on-demand vs. pre-materialized). `Alphabetizer` never iterates over shifts directly; it calls `CircularShifter.get_shift()`.

3. `Alphabetizer` hides the sort algorithm. Swap quicksort for a collation-aware Unicode sort — touch only `Alphabetizer`.

4. `Output` hides rendering. Add a JSON output mode — touch only `Output`.

**Criteria satisfied:** C1 (each module has one secret), C2 (design decisions hidden), C4 (each concern in one place), C9 (structure reflects domain decisions, not processing steps).

**What a non-elite answer looks like:** Decomposing by pipeline stage (Input → Shifter → Sorter → Output), where all stages share a global data structure. This feels natural but creates tight coupling: any change to the shared structure ripples everywhere.

---

### Gold 2 — Hexagonal Architecture: E-Commerce Order Service

**PROMPT:**
> Design the internal architecture of an Order Service in a microservices system.
> The service must: accept orders via REST API, persist to PostgreSQL, publish
> OrderPlaced events to Kafka, send confirmation emails, and be fully testable
> without any infrastructure running.

**ELITE ANSWER:**

Structure using hexagonal architecture (Cockburn, 2005) + Clean Architecture dependency rule (Martin, 2012):

```
order-service/
├── domain/                        # Inner ring — zero infrastructure imports
│   ├── order.py                   # Order aggregate, OrderLine value object
│   ├── order_id.py                # Strongly-typed wrapper: OrderId(uuid)
│   ├── events.py                  # OrderPlaced domain event (pure data)
│   └── order_repository.py        # Port (interface only): find, save
│
├── application/                   # Use cases — depends only on domain
│   ├── place_order.py             # PlaceOrderCommand, PlaceOrderHandler
│   ├── cancel_order.py            # CancelOrderCommand, CancelOrderHandler
│   └── ports/
│       ├── event_publisher.py     # Port: publish(event: DomainEvent) -> None
│       └── email_sender.py        # Port: send_confirmation(order: Order) -> None
│
├── infrastructure/                # Outer ring — depends on application ports
│   ├── postgres_order_repo.py     # Adapter: implements order_repository.OrderRepository
│   ├── kafka_event_publisher.py   # Adapter: implements event_publisher.EventPublisher
│   ├── smtp_email_sender.py       # Adapter: implements email_sender.EmailSender
│   └── in_memory/
│       ├── fake_order_repo.py     # In-memory adapter for tests
│       ├── recording_publisher.py # Captures events in a list for assertions
│       └── fake_email_sender.py   # Captures emails in a list for assertions
│
└── interface/                     # Driving adapters
    ├── rest/
    │   ├── order_routes.py        # Flask/FastAPI routes — thin; delegates to use cases
    │   └── dto.py                 # Request/response shapes (NOT domain objects)
    └── cli/
        └── admin_cli.py           # Alternative driver for the same use cases
```

**Key design decisions:**

**1. The domain has no infrastructure imports:**
```python
# domain/order.py
from dataclasses import dataclass, field
from typing import List
from .order_id import OrderId
from .events import OrderPlaced

@dataclass
class Order:
    id: OrderId
    customer_id: str
    lines: List[OrderLine] = field(default_factory=list)
    status: str = "PENDING"
    _events: List = field(default_factory=list, repr=False)

    def place(self) -> None:
        if not self.lines:
            raise ValueError("Cannot place an order with no lines")
        self.status = "PLACED"
        self._events.append(OrderPlaced(order_id=self.id, lines=self.lines))

    def collect_events(self) -> List:
        events, self._events = self._events, []
        return events
```
Notice: no SQLAlchemy, no Django, no Pydantic — just Python dataclasses. The `Order` aggregate enforces its own invariant (no empty orders) and emits domain events through a collection on itself.

**2. The use case orchestrates through ports:**
```python
# application/place_order.py
from domain.order_repository import OrderRepository
from application.ports.event_publisher import EventPublisher
from application.ports.email_sender import EmailSender

class PlaceOrderHandler:
    def __init__(
        self,
        repo: OrderRepository,
        publisher: EventPublisher,
        emailer: EmailSender,
    ):
        self._repo = repo
        self._publisher = publisher
        self._emailer = emailer

    def handle(self, cmd: PlaceOrderCommand) -> OrderId:
        order = Order.create(cmd.customer_id, cmd.lines)
        order.place()  # domain logic fires here
        self._repo.save(order)
        for event in order.collect_events():
            self._publisher.publish(event)
        self._emailer.send_confirmation(order)
        return order.id
```
The handler does not import `psycopg2`, `kafka-python`, or `smtplib`. It receives those capabilities through injected port interfaces.

**3. The REST adapter is thin:**
```python
# interface/rest/order_routes.py
@router.post("/orders", status_code=201)
def place_order(body: PlaceOrderRequest, handler: PlaceOrderHandler = Depends(get_handler)):
    try:
        order_id = handler.handle(PlaceOrderCommand(
            customer_id=body.customer_id,
            lines=[OrderLine(sku=l.sku, qty=l.qty) for l in body.lines]
        ))
        return {"order_id": str(order_id)}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
```

**4. Tests run with no infrastructure:**
```python
def test_place_order_publishes_event():
    repo = FakeOrderRepository()
    publisher = RecordingPublisher()
    emailer = FakeEmailSender()
    handler = PlaceOrderHandler(repo, publisher, emailer)

    order_id = handler.handle(PlaceOrderCommand(
        customer_id="C-1",
        lines=[OrderLine(sku="SKU-A", qty=2)]
    ))

    assert len(publisher.published) == 1
    assert isinstance(publisher.published[0], OrderPlaced)
    assert publisher.published[0].order_id == order_id
```
Zero database. Zero network. Instant. Deterministic.

**Criteria satisfied:** C1, C2, C3 (domain has no outward imports), C4, C5 (ports and adapters, infrastructure-free tests), C8 (type-safe identifiers, invalid Order cannot be placed), C9 (package structure reflects architecture).

---

### Gold 3 — DDD Bounded Contexts: E-Commerce Platform

**PROMPT:**
> An e-commerce platform manages customers, product catalog, orders, shipping,
> payments, and promotions. Different teams own these areas. Design the bounded
> context map and explain the integration strategy between contexts.

**ELITE ANSWER:**

**The core insight (Evans, 2003):** "Order" is not one thing. In the Sales context, an Order is a customer commitment with line items and a price. In the Fulfillment context, it's a picking list with warehouse locations. In the Finance context, it's a liability with a payment schedule. If you build one `Order` class shared by all three contexts, every team will fight over the model. The correct move is to allow each context to own its own `Order` model, united only by a stable `order_id`.

**Bounded Context Map:**

```
┌─────────────────────────────────────────────────────────────────┐
│                        E-Commerce Platform                       │
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Catalog BC     │    │   Identity BC     │                   │
│  │  (Products,      │    │  (Customer,       │                   │
│  │   Pricing,       │    │   Auth,           │                   │
│  │   Inventory)     │    │   Preferences)    │                   │
│  └──────┬───────────┘    └──────┬────────────┘                  │
│         │ ACL                   │ ACL                            │
│  ┌──────▼───────────────────────▼────────────┐                  │
│  │            Sales BC (Core Domain)          │                  │
│  │   Order, Cart, Checkout, Promotions        │                  │
│  │   Ubiquitous language: "place", "confirm"  │                  │
│  └──────┬────────────────────────┬────────────┘                  │
│         │ Domain Events          │ Domain Events                 │
│         │ OrderPlaced            │ OrderPlaced                   │
│  ┌──────▼────────────┐   ┌───────▼────────────┐                 │
│  │  Fulfillment BC   │   │    Finance BC       │                 │
│  │  (Shipment,       │   │    (Invoice,        │                 │
│  │   PickList,       │   │     Payment,        │                 │
│  │   Carrier,        │   │     Refund,         │                 │
│  │   Tracking)       │   │     Tax)            │                 │
│  └───────────────────┘   └─────────────────────┘                │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                  Notifications BC (Generic)                │   │
│  │              (Email, SMS, Push — pure infrastructure)      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Integration patterns between contexts:**

**Sales → Fulfillment (Downstream conformist):**
Fulfillment reacts to `OrderPlaced` domain events published by Sales. Fulfillment builds its own `PickingOrder` model from the event data — it does not import Sales types.
```python
# fulfillment/application/handlers.py
def on_order_placed(event: OrderPlacedEvent) -> None:
    # Fulfillment's own model, Fulfillment's own vocabulary
    picking_order = PickingOrder.create(
        reference=PickingOrderRef(event.order_id),  # identity link
        items=[PickItem(sku=l.sku, qty=l.qty) for l in event.lines],
    )
    picking_repo.save(picking_order)
```

**Sales → Finance (Downstream conformist via ACL):**
Finance subscribes to `OrderPlaced` events. It translates via an Anti-Corruption Layer (ACL) to prevent Sales's model vocabulary from leaking into Finance:
```python
# finance/infrastructure/sales_acl.py
class SalesEventTranslator:
    def to_invoice_command(self, event: OrderPlacedEvent) -> CreateInvoiceCommand:
        return CreateInvoiceCommand(
            order_ref=OrderRef(event.order_id),
            amount=Money(event.total_amount, event.currency),
            customer_ref=CustomerRef(event.customer_id),
        )
```

**Catalog → Sales (Customer/Supplier or Published Language):**
Sales queries Catalog for product information at checkout time. Catalog publishes a stable schema (the Published Language) — a versioned contract independent of Catalog's internal model. Sales is a downstream customer; Catalog is the upstream supplier. Catalog must not break its published schema without versioning.

**Why not share a single `Order` class across all contexts?**
Because the invariants conflict. Finance's `Order` must carry VAT breakdown and payment terms — irrelevant to Fulfillment. Fulfillment's `Order` must carry warehouse bin location — irrelevant to Finance. A shared model becomes a God Object that everyone owns and no one can safely change. Separate models, stable identifiers, explicit integration contracts: this is the DDD answer.

**Criteria satisfied:** C1, C2, C4, C7 (each team owns one context), C9 (structure = domain areas, not layers).

---

### Gold 4 — REST API Design: Correct Resource Modeling

**PROMPT:**
> Design the REST API for a project management system with projects, tasks,
> and comments. Include: resource naming, HTTP verb semantics, status codes,
> and pagination. Explain what makes it genuinely REST and not just RPC-over-HTTP.

**ELITE ANSWER:**

**The foundational distinction (Fielding, 2000):** REST resources are *nouns*, not verbs. HTTP verbs carry the semantic meaning. A URL `/createTask` is RPC over HTTP — it bakes the verb into the resource name, making GET/POST semantics meaningless. An elite REST API models the domain as resources and delegates verb meaning to HTTP.

**Resource hierarchy:**

```
Projects are top-level resources:
  GET    /projects                   → list all accessible projects (paginated)
  POST   /projects                   → create a project
  GET    /projects/{projectId}       → get project details
  PATCH  /projects/{projectId}       → partial update (title, description)
  DELETE /projects/{projectId}       → archive (soft delete in most systems)

Tasks belong to a project:
  GET    /projects/{projectId}/tasks           → list tasks (paginated, filterable)
  POST   /projects/{projectId}/tasks           → create task
  GET    /projects/{projectId}/tasks/{taskId}  → get task
  PATCH  /projects/{projectId}/tasks/{taskId}  → update (title, assignee, due_date)
  DELETE /projects/{projectId}/tasks/{taskId}  → delete task

Comments belong to a task:
  GET    /projects/{projectId}/tasks/{taskId}/comments
  POST   /projects/{projectId}/tasks/{taskId}/comments
  DELETE /projects/{projectId}/tasks/{taskId}/comments/{commentId}
```

**State transitions as sub-resources (not verbs in URLs):**
Task status transitions are not `POST /tasks/123/complete`. Status is a field on the task. The client sends:
```
PATCH /projects/{projectId}/tasks/{taskId}
Body: {"status": "COMPLETED"}
```
This preserves the resource model. The server validates the transition (can't go from COMPLETED to IN_PROGRESS without reopening). If you need explicit state machine documentation, use a `transitions` sub-resource for discovery — but the actual change is still a PATCH on the resource.

**HTTP semantics:**
```
GET    → Safe, idempotent. Never triggers side effects. Cacheable.
POST   → Non-idempotent creation. Returns 201 Created with Location header.
PATCH  → Partial update, idempotent per RFC 5789. Returns 200 with updated resource.
DELETE → Idempotent. Returns 204 No Content (or 200 if returning deleted state).
PUT    → Full replacement. Use sparingly; idempotent but dangerous for partial writes.
```

**Status codes:**
```
201 Created          → POST success. Always include Location: /projects/42
200 OK               → GET, PATCH success with body
204 No Content       → DELETE success, or PATCH with no response body
400 Bad Request      → Validation failure. Body: {"errors": [{"field": "title", "msg": "required"}]}
401 Unauthorized     → No valid authentication credential
403 Forbidden        → Authenticated but not authorized for this resource
404 Not Found        → Resource does not exist (or client is not authorized to know it exists)
409 Conflict         → Optimistic lock failure; concurrent update detected
422 Unprocessable    → Well-formed request but semantic validation fails
429 Too Many Requests → Rate limiting. Include Retry-After header.
```

**Pagination (cursor-based, not offset):**
```json
GET /projects/42/tasks?limit=25&cursor=eyJpZCI6MTAwfQ==

Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTI1fQ==",
    "has_more": true,
    "limit": 25
  }
}
```
Reason for cursor over offset: offset pagination breaks when rows are inserted/deleted between pages. Cursor is stable.

**What makes this REST and not RPC-over-HTTP:**
1. URLs name resources (nouns). HTTP verbs carry action semantics.
2. Responses are self-describing (Content-Type, status codes).
3. State transitions are PATCH on a resource, not `/do-the-thing` endpoints.
4. Stateless: every request carries auth (Bearer token). No server session.
5. Cacheable: GET responses carry Cache-Control headers appropriate to the data's volatility.

**What non-elite looks like:** `POST /api/doCreateTask`, `GET /api/getProjectById?id=42`, `POST /api/updateTaskStatus` with a body `{"action": "complete"}`. This is RPC over HTTP — it wastes HTTP's semantics and loses cacheability, idempotency guarantees, and uniform interface.

**Criteria satisfied:** C4 (concerns separated by layer), C8 (correct usage is natural — wrong verbs return 405 Method Not Allowed automatically).

---

### Gold 5 — Event-Driven / CQRS Architecture: Order Processing

**PROMPT:**
> Design a CQRS + event-sourced architecture for an Order service that must
> support: placing orders, checking stock (via an external Inventory service),
> charging payment (external Payment service), and serving an order dashboard
> with read-optimized views. Explain the consistency model and failure modes.

**ELITE ANSWER:**

**The core principle (Hohpe, 2003; Vernon, 2013; Helland, 2005):** Separate the write model (enforces invariants, emits events) from the read model (optimized projections for queries). Events are the source of truth. Services communicate through events, not synchronous RPC chains.

**Architecture:**

```
WRITE SIDE (command model)
─────────────────────────
Client → POST /orders (PlaceOrderCommand)
       ↓
OrderCommandHandler
  1. Load Order aggregate from EventStore by order_id
     (replay: OrderCreated → ItemsAdded → ... → current state)
  2. Call order.place() — validates domain rules, emits OrderPlaced event
  3. Append OrderPlaced to EventStore (single atomic write)
  4. EventStore publishes to Kafka: topic=order-events
  → Return 202 Accepted + order_id
     (the order is not yet confirmed — eventual consistency is explicit)

EventStore schema:
  (stream_id: UUID, version: int, event_type: str, payload: bytes, timestamp)
  PRIMARY KEY (stream_id, version)  ← optimistic concurrency control

READ SIDE (query model — projections)
──────────────────────────────────────
Kafka Consumer: OrderProjectionBuilder
  Reads from topic=order-events
  On OrderPlaced → upsert into read_db.orders_view
  On PaymentConfirmed → update orders_view.payment_status = CONFIRMED
  On ShipmentDispatched → update orders_view.shipment_status = DISPATCHED

Client → GET /orders/{id} (queries read model directly, not EventStore)
  ↓
orders_view: {order_id, customer_id, status, payment_status, shipment_status, ...}
  Millisecond reads. Denormalized for the query. No joins needed.

INTER-SERVICE CHOREOGRAPHY (not orchestration)
───────────────────────────────────────────────
Order Service publishes:   OrderPlaced (topic: order-events)
Inventory Service reacts:  StockReserved OR StockInsufficient
Payment Service reacts:    PaymentCharged OR PaymentFailed

Order Service subscribes to: inventory-events, payment-events
On StockReserved    → order.confirm_stock(); append StockConfirmed
On StockInsufficient → order.cancel("INSUFFICIENT_STOCK"); append OrderCancelled
On PaymentCharged   → order.confirm_payment(); append PaymentConfirmed
On PaymentFailed    → order.cancel("PAYMENT_FAILED"); append OrderCancelled
```

**Optimistic concurrency in the EventStore:**
```python
def append_event(stream_id: UUID, expected_version: int, event: DomainEvent):
    try:
        db.execute("""
            INSERT INTO events (stream_id, version, event_type, payload)
            VALUES (%s, %s, %s, %s)
        """, (stream_id, expected_version + 1, event.type, serialize(event)))
    except UniqueViolationError:
        raise ConcurrentModificationError(
            f"Stream {stream_id} was modified concurrently at version {expected_version}"
        )
```
Two handlers trying to append to the same order stream at the same version will have one succeed and one raise — no lost updates.

**Failure modes and mitigations:**

| Failure | Consequence | Mitigation |
|---------|-------------|------------|
| Kafka broker down during publish | Event written to EventStore but not published | Outbox pattern: write event to DB table alongside aggregate; separate publisher reads from outbox |
| Inventory consumer crashes mid-processing | Event is re-delivered (at-least-once delivery) | Make handlers **idempotent** using event's event_id as deduplication key in a processed_events table |
| Payment service permanently fails | Order stuck in AWAITING_PAYMENT | Timeout saga: a scheduled job emits PaymentTimeout after N minutes; Order cancels and stock is released |
| Read model projection lags | Dashboard shows stale data | Acceptable under eventual consistency — surface lag indicator in UI; reads are explicitly marked as "as of {timestamp}" |

**Consistency model:**
- **Within a single Order aggregate:** Strong consistency. The EventStore append is atomic.
- **Across Order, Inventory, Payment:** Eventual consistency via choreography. No distributed transaction. The saga pattern handles compensation.
- **The explicit contract:** `POST /orders` returns 202, not 201. The order is *received*, not confirmed. The client polls or subscribes to updates.

**Why choreography over orchestration (Hohpe, 2003):**
An orchestrator (e.g., a Saga Orchestrator that calls Inventory.reserveStock() then Payment.charge()) accrues all the coupling. If the orchestrator changes, all flows change. In choreography, each service reacts to events independently. Inventory does not know that Order Service exists; it only knows about `OrderPlaced` events. This is the loosest possible coupling.

**Criteria satisfied:** C1, C2, C3 (no cross-context schema sharing), C4, C7 (each service owned by one team), C8 (idempotency makes the right thing safe by default).

---

## 4. AUDIT: Python Pseudocode for Eliteness Gating

This audit gates whether a generated architecture answer achieves elite quality.
Run it on the candidate answer text. Fail the sample if any gate fails.

```python
"""
elite_architecture_audit.py

Audit function for architecture SFT gold.
Input:  candidate_answer: str  (the model's answer to an architecture prompt)
Output: AuditResult with pass/fail per criterion and overall verdict.
"""

import re
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class AuditResult:
    passed: bool
    score: float  # 0.0–1.0
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ─── Criterion checkers ───────────────────────────────────────────────────────

def check_naming_quality(answer: str) -> Tuple[bool, str]:
    """
    C1/C9: Module/service names should be domain nouns, not technical dumpsters.
    Reject answers that rely heavily on 'Utils', 'Manager', 'Helper', 'Common'.
    """
    bad_names = re.findall(
        r'\b(Utils?|Manager|Helper|Common|Base(?:Service|Repo)?|Handler(?:Impl)?)\b',
        answer, re.IGNORECASE
    )
    # Allow 1–2 occurrences (might appear in a negative example)
    if len(bad_names) > 2:
        return False, f"Found {len(bad_names)} god-class/helper names: {set(bad_names)}"
    return True, ""


def check_dependency_direction(answer: str) -> Tuple[bool, str]:
    """
    C3: The answer must mention that dependencies point inward / toward the domain.
    Absence of this is a hard fail for architecture questions.
    """
    signals = [
        r"depend\w* (point|flow|direct)\w* inward",
        r"domain.*no.*import",
        r"inner.*ring.*know.*nothing",
        r"dependency.*rule",
        r"dependency.*inversion",
        r"domain.*layer.*zero.*infrastructure",
        r"infrastructure.*depend.*domain",  # correct direction stated
    ]
    hits = sum(1 for s in signals if re.search(s, answer, re.IGNORECASE))
    if hits == 0:
        return False, "Dependency direction never stated. Elite answers specify which direction dependencies point."
    return True, ""


def check_information_hiding(answer: str) -> Tuple[bool, str]:
    """
    C2: The answer must show that implementation details are hidden behind interfaces/ports.
    Look for: interface, port, adapter, abstraction, hidden, secret, encapsulate.
    """
    signals = [
        r'\binterface\b', r'\bport\b', r'\badapter\b',
        r'\babstraction\b', r'\bhid\w+\b', r'\bencapsulat\w+\b',
        r'\bsecret\b',  # Parnas's term
    ]
    hits = sum(1 for s in signals if re.search(s, answer, re.IGNORECASE))
    if hits < 2:
        return False, "Information hiding not demonstrated. Answer should show interfaces/ports concealing implementations."
    return True, ""


def check_cohesion_coupling(answer: str) -> Tuple[bool, str]:
    """
    C1: High cohesion / low coupling must be explicitly addressed.
    """
    cohesion_hit = bool(re.search(r'\bcohesion\b', answer, re.IGNORECASE))
    coupling_hit = bool(re.search(r'\bcoupling\b', answer, re.IGNORECASE))
    loose_hit = bool(re.search(r'loose\w*\s+coup\w+|decoupl\w+', answer, re.IGNORECASE))
    if not (cohesion_hit or loose_hit):
        return False, "Cohesion not discussed. Elite answers address high cohesion explicitly."
    if not (coupling_hit or loose_hit):
        return False, "Coupling not discussed. Elite answers address low coupling explicitly."
    return True, ""


def check_separation_of_concerns(answer: str) -> Tuple[bool, str]:
    """
    C4: Domain logic / business rules must be separated from infrastructure.
    """
    signals = [
        r"separat\w+ of concerns",
        r"business.*logic.*not.*infra",
        r"domain.*layer",
        r"domain.*model.*no.*database",
        r"domain.*no.*framework",
        r"no.*sql.*in.*controller",
        r"single.*responsibility",
    ]
    hits = sum(1 for s in signals if re.search(s, answer, re.IGNORECASE))
    if hits == 0:
        return False, "Separation of concerns not addressed. Domain/infrastructure separation is required."
    return True, ""


def check_reasoning_present(answer: str) -> Tuple[bool, str]:
    """
    Elite answers explain WHY, not just what.
    Look for causal language: "because", "so that", "this means", "the reason",
    "without this", "otherwise", "which ensures".
    """
    causal_patterns = [
        r'\bbecause\b', r'\bso that\b', r'\bthis means\b',
        r'\bthe reason\b', r'\bwithout this\b', r'\botherwise\b',
        r'\bwhich ensures\b', r'\bthis allows\b', r'\bthis prevents\b',
    ]
    hits = sum(1 for p in causal_patterns if re.search(p, answer, re.IGNORECASE))
    if hits < 3:
        return False, f"Only {hits} causal reasoning markers found. Elite answers explain WHY at each design decision."
    return True, ""


def check_concrete_structure(answer: str) -> Tuple[bool, str]:
    """
    Elite architecture answers include concrete structure:
    module names, package paths, code snippets, or dependency diagrams.
    Reject pure prose without any concrete artifact.
    """
    has_code_block = bool(re.search(r'```', answer))
    has_package_path = bool(re.search(r'[a-z_]+/[a-z_]+/[a-z_]+', answer))
    has_module_list = bool(re.search(r'\bmodule\b.*:.*\n.*\bmodule\b', answer, re.IGNORECASE))
    has_ascii_diagram = bool(re.search(r'[│─┌┐└┘├┤┬┴┼→←↑↓]', answer))

    if not (has_code_block or has_package_path or has_module_list or has_ascii_diagram):
        return False, "No concrete structure found (no code, no paths, no diagrams). Elite answers are concrete."
    return True, ""


def check_anti_pattern_awareness(answer: str) -> Tuple[bool, str]:
    """
    Elite answers either avoid anti-patterns or explicitly call out what NOT to do.
    """
    anti_pattern_signals = [
        r'god\s+(class|object)',
        r'big\s+ball\s+of\s+mud',
        r'spaghetti',
        r'anti.?pattern',
        r'wrong.*way',
        r'avoid',
        r'do not|don\'t',
        r'non.?elite|naive|common mistake',
        r'instead of',
    ]
    hits = sum(1 for s in anti_pattern_signals if re.search(s, answer, re.IGNORECASE))
    if hits == 0:
        return False, "No anti-pattern awareness. Elite answers contrast correct design with common mistakes."
    return True, ""


# ─── Degeneration / repetition guard ─────────────────────────────────────────

def check_repetition(answer: str) -> Tuple[bool, str]:
    """
    Guard against degenerate outputs: repetitive sentence fragments,
    copy-pasted blocks, or lists that merely repeat the same phrase.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', answer) if len(s.strip()) > 20]
    if len(sentences) < 5:
        return True, ""  # Too short to check meaningfully

    # Check for duplicate sentences
    seen = set()
    duplicates = []
    for s in sentences:
        normalized = re.sub(r'\s+', ' ', s.lower())
        if normalized in seen:
            duplicates.append(s[:60])
        seen.add(normalized)

    if len(duplicates) > 2:
        return False, f"Repetition detected: {len(duplicates)} duplicate sentences. Possible degeneration."

    # Check for list-only responses (bullet soup with no explanation)
    bullets = re.findall(r'^[\s]*[-*•]\s+.+$', answer, re.MULTILINE)
    non_bullet_words = len(re.sub(r'^[\s]*[-*•]\s+.+$', '', answer, flags=re.MULTILINE).split())
    if len(bullets) > 10 and non_bullet_words < 100:
        return False, "Answer is mostly bullets with minimal prose. Elite answers explain, not just list."

    return True, ""


def check_length(answer: str) -> Tuple[bool, str]:
    """
    Architecture answers must be substantive. Under 200 words is too thin.
    Over 5000 words without structure is likely unfocused.
    """
    words = len(answer.split())
    if words < 200:
        return False, f"Answer too short ({words} words). Elite architecture answers require substantive depth."
    if words > 5000:
        return False, f"Answer very long ({words} words). Check for repetition or scope creep."
    return True, ""


# ─── Named elite grounding check ─────────────────────────────────────────────

def check_elite_grounding(answer: str, require_names: int = 1) -> Tuple[bool, str]:
    """
    For explicit architecture questions, the answer should cite or reference
    at least one named architect or canonical text.
    (Relaxed criterion — applied only when the answer is expected to justify choices.)
    """
    elite_names = [
        "Parnas", "Alexander", "Martin", "Clean Architecture",
        "Evans", "DDD", "Domain-Driven", "Cockburn", "hexagonal",
        "Fowler", "Conway", "Beck", "Hohpe", "Newman", "Fielding",
        "REST", "Liskov", "LSP", "Brooks", "Lamport", "Hickey",
        "Armstrong", "Helland", "Feathers", "Gang of Four", "SOLID",
    ]
    hits = [name for name in elite_names if re.search(name, answer, re.IGNORECASE)]
    if len(hits) < require_names:
        return False, f"No elite architectural references found. Answers should cite canonical sources or principles."
    return True, ""


# ─── Master audit function ────────────────────────────────────────────────────

CHECKS = [
    ("naming_quality",         check_naming_quality,         1.0),
    ("dependency_direction",   check_dependency_direction,   1.5),  # weighted
    ("information_hiding",     check_information_hiding,     1.5),
    ("cohesion_coupling",      check_cohesion_coupling,      1.0),
    ("separation_of_concerns", check_separation_of_concerns, 1.0),
    ("reasoning_present",      check_reasoning_present,      1.5),
    ("concrete_structure",     check_concrete_structure,     1.5),
    ("anti_pattern_awareness", check_anti_pattern_awareness, 1.0),
    ("repetition_guard",       check_repetition,             1.0),
    ("length_check",           check_length,                 1.0),
]

HARD_FAIL_CHECKS = {
    "dependency_direction",    # Must always pass for architecture questions
    "concrete_structure",      # Pure prose without structure is never elite
    "repetition_guard",        # Degeneration is immediate disqualification
    "length_check",
}


def audit_architecture_answer(
    answer: str,
    require_elite_names: bool = False,
) -> AuditResult:
    """
    Run all eliteness checks on the candidate answer.

    Returns AuditResult:
      .passed  — True if all hard-fail checks pass and score >= 0.75
      .score   — weighted fraction of checks passed (0.0–1.0)
      .failures — list of failure messages for failed checks
      .warnings — list of warning messages for soft failures
    """
    failures = []
    warnings = []
    total_weight = 0.0
    passed_weight = 0.0

    checks = list(CHECKS)
    if require_elite_names:
        checks.append(("elite_grounding", lambda a: check_elite_grounding(a, 1), 0.5))

    for name, fn, weight in checks:
        ok, msg = fn(answer)
        total_weight += weight
        if ok:
            passed_weight += weight
        else:
            if name in HARD_FAIL_CHECKS:
                failures.append(f"[HARD FAIL] {name}: {msg}")
            else:
                failures.append(f"[FAIL] {name}: {msg}")
        if not ok and name not in HARD_FAIL_CHECKS:
            warnings.append(msg)

    score = passed_weight / total_weight if total_weight > 0 else 0.0
    hard_fails = [f for f in failures if f.startswith("[HARD FAIL]")]

    passed = (len(hard_fails) == 0) and (score >= 0.75)

    return AuditResult(passed=passed, score=round(score, 3), failures=failures, warnings=warnings)


# ─── Usage example ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    SAMPLE = """
    Design your modules around information hiding (Parnas, 1972). Each module
    should hide one design decision behind a stable interface. Dependencies
    point inward toward the domain — the domain layer has zero infrastructure
    imports. Use ports and adapters (Cockburn) so you can run the application
    core under test without any database or network.

    src/
    ├── domain/
    │   ├── order.py           # Aggregate, emits domain events
    │   └── order_repo.py      # Port: interface only
    ├── application/
    │   └── place_order.py     # Use case — depends only on domain ports
    ├── infrastructure/
    │   ├── postgres_repo.py   # Adapter: implements order_repo port
    │   └── fake_repo.py       # In-memory adapter for tests
    └── interface/
        └── rest_routes.py     # Thin HTTP adapter

    Avoid the God class anti-pattern — if you have a "ServiceHelper" you have
    separated by layer, not by concern. This is wrong because it means every
    concern is mixed into every layer. Instead, separate by domain concept.
    The domain must not import sqlalchemy, flask, or any framework — because
    those are infrastructure decisions that should be changeable without
    touching business logic. This allows swapping PostgreSQL for DynamoDB
    by only touching the infrastructure adapter.
    """

    result = audit_architecture_answer(SAMPLE, require_elite_names=True)
    print(f"Passed: {result.passed}")
    print(f"Score:  {result.score}")
    if result.failures:
        print("Failures:")
        for f in result.failures:
            print(f"  {f}")
```

---

## QUICK REFERENCE: Elite Pattern → Architect(s)

| Pattern / Principle | Primary Architect(s) | Checkable Signal |
|---|---|---|
| Information hiding | Parnas | One module, one secret, stable interface |
| High cohesion / low coupling | Parnas, Newman | Module has one noun name; few inter-module imports |
| Dependency rule | R.C. Martin | Domain has zero framework imports |
| Separation of concerns | Dijkstra, Evans | SQL not in controllers; domain not in infrastructure |
| Ports and adapters | Cockburn | Infrastructure-free test suite exists |
| Composition over inheritance | GoF | No deep hierarchies; inject strategies |
| Ubiquitous language | Evans | Code names match domain expert vocabulary |
| Bounded contexts | Evans | Each model valid only within its boundary |
| Reverse Conway maneuver | Conway, Newman | Team per service; no shared ownership |
| Simple design (YAGNI) | Beck | Fewest elements that pass tests |
| Stateless uniform interface | Fielding | No server session; nouns in URLs, verbs are HTTP methods |
| Make right thing easy | R. Mariani, Beck | Wrong usage is a type error or compile error |
| Let it crash / supervision | J. Armstrong | Supervisor tree is explicit; no defensive catch-all |
| Outside data is immutable | Helland | Events/messages are versioned, append-only |
| Reduce essential complexity | Brooks | Every abstraction earns its keep |
| Strangler Fig migration | Fowler | New system surrounds old; traffic routed incrementally |

---

*Sources:*
- Christopher Alexander, *A Pattern Language* (1977)
- David Parnas, "On the Criteria..." (CACM, 1972)
- Fred Brooks, "No Silver Bullet" (1986)
- Melvin Conway, "How Do Committees Invent?" (Datamation, 1968)
- Gamma, Helm, Johnson, Vlissides, *Design Patterns* (1994)
- Robert C. Martin, *Clean Architecture* (2017); blog post (2012)
- Alistair Cockburn, "Hexagonal Architecture" (2005)
- Roy Fielding, doctoral dissertation Ch. 5 (2000)
- Eric Evans, *Domain-Driven Design* (2003)
- Martin Fowler, *Refactoring* (1999, 2018); *PEAA* (2002)
- Kent Beck, *XP Explained* (1999); *TDD: By Example* (2002)
- Gregor Hohpe & Bobby Woolf, *Enterprise Integration Patterns* (2003)
- Sam Newman, *Building Microservices* (2nd ed., 2021)
- Leslie Lamport, "Time, Clocks..." (CACM, 1978); *Specifying Systems* (2002)
- Rich Hickey, "Simple Made Easy" (Strange Loop, 2011)
- Joe Armstrong, doctoral thesis (2003); *Programming Erlang* (2007)
- Pat Helland, "Data on the Outside vs. Inside" (CIDR, 2005); "Immutability Changes Everything" (CIDR, 2015)
- Michael Feathers, *Working Effectively with Legacy Code* (2004)
- Barbara Liskov, "Data Abstraction and Hierarchy" (OOPSLA, 1987)
- Edsger Dijkstra, "Goto Statement Considered Harmful" (CACM, 1968)
