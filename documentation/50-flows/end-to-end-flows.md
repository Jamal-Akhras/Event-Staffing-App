# End-to-End Flows

These flows show what people experience and where the system protects them. Detailed endpoint names are in the [endpoint reference](../40-api/endpoint-reference.md).

## Worker onboarding

```mermaid
flowchart TD
    A[Worker registers] --> B[User and empty worker profile created]
    B --> C[Verification email queued]
    C --> D[Worker signs in]
    D --> E{Profile complete?}
    E -->|No| F[Onboarding: identity, role, city/market and experience]
    E -->|Yes| G[Browse feed]
    F --> G
    G --> H{Email verified?}
    H -->|No| I[Can browse, cannot create marketplace/trust actions]
    H -->|Yes| J[Can apply, message, upload, rate and report]
```

## Venue onboarding

```mermaid
flowchart TD
    A[Operator obtains invite code] --> B[Selects active market]
    B --> C[Registers organisation and venue]
    C --> D[Organisation, venue, owner membership and user commit together]
    D --> E[Verification email queued]
    E --> F[Operator enters protected dashboard]
    F --> G[Completes venue profile]
    G --> H[Creates first shift or template]
```

The invite only permits operator registration. It does not grant founding-partner pricing.

## Shift-to-payment journey

```mermaid
sequenceDiagram
    participant V as Venue web
    participant API
    participant W as Worker mobile
    participant JOB as Background worker

    V->>API: Create open shift
    API-->>W: Shift appears in market feed
    W->>API: Apply
    API-->>V: Application notification
    V->>API: Approve application
    API-->>V: Booking created, capacity reserved
    API-->>W: Approval notification
    V->>API: Confirm booking
    W->>API: Check in
    W->>API: Check out
    V->>API: Approve completed work
    V->>W: Pay outside platform
    V->>API: Record payment attestation
    API-->>W: Earnings record updated
    JOB-->>V: Rating prompt
    JOB-->>W: Rating prompt
```

## Application decision under concurrency

```mermaid
sequenceDiagram
    participant O1 as Operator request A
    participant O2 as Operator request B
    participant DB as PostgreSQL shift row

    O1->>DB: Lock shift
    O2->>DB: Wait for lock
    O1->>DB: Approve and consume final place
    O1->>DB: Commit
    DB-->>O2: Lock acquired; capacity now full
    O2-->>O2: Reject with conflict/validation result
```

Without the lock, both requests could see one empty place and both approve. The database-backed flow prevents that race.

## Cancellation and closure

```mermaid
flowchart TD
    Change[Venue needs to change a shift] --> Started{Has work started?}
    Started -->|Yes| Manual[Do not rewrite as cancellation; handle operational exception]
    Started -->|No| Choice{Close or cancel?}
    Choice -->|Close| Close[Reject pending applications; preserve bookings]
    Choice -->|Cancel| Reason[Require reason and authenticated actor]
    Reason --> Cancel[Cancel requested/confirmed bookings]
    Cancel --> Notify[Queue worker notifications]
    Cancel --> Zero[Set shift cancelled and capacity to zero]
```

A worker may withdraw only a pending application before start. A booked worker may cancel only a requested/confirmed booking and must give a reason. The venue receives a durable notification.

## No-show processing

```mermaid
flowchart LR
    Scheduler[15-minute scheduler] --> Query[Find confirmed bookings]
    Query --> Window{Check-in window expired?}
    Window -->|No| Keep[Leave confirmed]
    Window -->|Yes| NoShow[Mark no-show]
    NoShow --> Capacity[Decrement filled capacity]
    Capacity --> Reliability[Recompute worker reliability]
    Reliability --> Notify[Notify venue]
```

## Notification delivery

```mermaid
flowchart LR
    Action[Committed business action] --> Event[Outbox event]
    Event --> Fanout[Resolve recipients and preferences]
    Fanout --> InApp[In-app inbox]
    Fanout --> Email[Email]
    Fanout --> Push[Push]
    InApp --> DeepLink[Open exact entity]
    Push --> DeepLink
    Email --> WebLink[Open web flow]
```

Provider failure does not roll back the original business action. The worker retries and eventually dead-letters repeated failures for investigation.

## Account export and deactivation

```mermaid
sequenceDiagram
    participant U as User
    participant API
    participant DB
    participant Store as Object storage

    U->>API: Confirm password and request export
    API->>DB: Gather identity and related records
    API-->>U: Structured export
    U->>API: Confirm password and deactivate
    API->>DB: Disable user, revoke sessions, anonymise profile
    DB-->>API: Commit
    API->>Store: Retire personal avatar after commit
```

## Report and dispute flow

```mermaid
flowchart LR
    User[Verified worker/operator] --> Report[Submit category, subject and description]
    Report --> Own[Reporter can track own report]
    Report --> Queue[System review queue]
    Queue --> Review[Reviewing]
    Review --> Resolve[Resolved]
    Review --> Dismiss[Dismissed with notes]
```

The API flow exists. Human triage ownership, evidence rules, response targets and a staff UI are still required.
