<!-- Alexander (patterns, "quality without a name") · Parnas (information hiding) · Uncle Bob (the dependency
     rule) · ports & adapters. The structure makes the right thing easy and the wrong thing hard. -->

# Order service — hexagonal (ports & adapters)

The **domain** (`Order`, `Money`, `Inventory`) knows nothing about HTTP, SQL, or Stripe. It owns the *ports*
— interfaces phrased in its own language:

```
OrderRepository:  save(order) · find(id) -> Order
PaymentGateway:   charge(money, source) -> Receipt
```

**Adapters** implement those ports at the edge, and depend inward:

```
HttpOrderController ──calls──▶ PlaceOrder (use-case) ──uses──▶ OrderRepository (port)
                                                      └─uses──▶ PaymentGateway (port)
PostgresOrderRepository ──implements──▶ OrderRepository
StripePaymentGateway    ──implements──▶ PaymentGateway
```

**The dependency rule (Uncle Bob):** every source dependency points *inward*, toward the domain. The domain
is pure — no imports of `psycopg`, `requests`, or `stripe` — so it is testable in isolation and unchanged when
you swap Postgres for SQLite or Stripe for a fake.

**Why it's elite (Parnas + Alexander):** each module hides one decision behind a stable interface (information
hiding), so a change to the database is a change to *one* adapter, never a ripple through business logic. The
shape of the system makes the correct dependency direction the path of least resistance — "quality without a
name." High cohesion inside each hexagon, low coupling across the ports.
