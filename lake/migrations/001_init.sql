-- Clean zone of the data lake (Cloud SQL for PostgreSQL).
-- Raw files live in GCS; document.storage_path points at them.

CREATE TABLE source (
    id               BIGSERIAL PRIMARY KEY,
    kind             TEXT NOT NULL CHECK (kind IN ('api', 'website', 'da_portal', 'email', 'manual')),
    domain           TEXT,
    terms_checked_on DATE,
    checked_by       TEXT,
    notes            TEXT
);

CREATE TABLE development (
    id                  BIGSERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    developer           TEXT,
    address             TEXT,
    suburb              TEXT,
    lga                 TEXT,
    state               TEXT CHECK (state IN ('QLD', 'NSW')),
    lat                 DOUBLE PRECISION,
    lng                 DOUBLE PRECISION,
    da_number           TEXT,
    total_lots          INTEGER,
    expected_completion DATE,
    hard_to_reach       BOOLEAN NOT NULL DEFAULT FALSE,  -- eligible for option B inquiries
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE stage (
    id                  BIGSERIAL PRIMARY KEY,
    development_id      BIGINT NOT NULL REFERENCES development(id),
    name                TEXT NOT NULL,
    lots                INTEGER,
    construction_status TEXT,
    UNIQUE (development_id, name)
);

CREATE TABLE lot (
    id            BIGSERIAL PRIMARY KEY,
    stage_id      BIGINT NOT NULL REFERENCES stage(id),
    lot_no        TEXT NOT NULL,
    property_type TEXT NOT NULL CHECK (property_type IN ('apartment', 'townhouse', 'house_and_land', 'land', 'other')),
    level         INTEGER,
    beds          NUMERIC(3,1),
    baths         NUMERIC(3,1),
    cars          INTEGER,
    internal_m2   NUMERIC(8,2),
    external_m2   NUMERIC(8,2),
    land_m2       NUMERIC(10,2),
    aspect        TEXT,
    UNIQUE (stage_id, lot_no)
);

CREATE TABLE document (
    id           BIGSERIAL PRIMARY KEY,
    source_id    BIGINT REFERENCES source(id),
    kind         TEXT NOT NULL CHECK (kind IN ('price_list', 'brochure', 'email', 'web_page', 'other')),
    sha256       CHAR(64) NOT NULL UNIQUE,
    media_type   TEXT,
    storage_path TEXT NOT NULL,   -- gs://bucket/path, internal only, never republished
    received_at  TIMESTAMPTZ NOT NULL,
    document_date DATE
);

CREATE TABLE price_observation (
    id          BIGSERIAL PRIMARY KEY,
    lot_id      BIGINT NOT NULL REFERENCES lot(id),
    observed_on DATE NOT NULL,     -- date of the document, not of processing
    price_aud   INTEGER,
    status      TEXT NOT NULL CHECK (status IN ('available', 'held', 'sold', 'unknown')),
    incentives  TEXT[],
    document_id BIGINT NOT NULL REFERENCES document(id),
    confidence  REAL,
    UNIQUE (lot_id, document_id)
);

-- Published sales contacts only. No personal profiles.
CREATE TABLE contact (
    id              BIGSERIAL PRIMARY KEY,
    agency          TEXT NOT NULL,
    contact_name    TEXT,
    role_email      TEXT NOT NULL UNIQUE,
    phone           TEXT,
    source_id       BIGINT REFERENCES source(id),
    suppressed      BOOLEAN NOT NULL DEFAULT FALSE,
    suppressed_at   TIMESTAMPTZ,
    last_contact_at TIMESTAMPTZ   -- delete after 24 months without contact
);

CREATE TABLE inquiry (
    id             BIGSERIAL PRIMARY KEY,
    development_id BIGINT NOT NULL REFERENCES development(id),
    contact_id     BIGINT NOT NULL REFERENCES contact(id),
    option         CHAR(1) NOT NULL CHECK (option IN ('A', 'B')),
    subject        TEXT NOT NULL,
    body           TEXT NOT NULL,
    status         TEXT NOT NULL,
    approved_by    TEXT,
    approved_at    TIMESTAMPTZ,
    sent_at        TIMESTAMPTZ,
    follow_ups     INTEGER NOT NULL DEFAULT 0,
    reply_class    TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE settlement (
    id         BIGSERIAL PRIMARY KEY,
    lot_id     BIGINT NOT NULL REFERENCES lot(id),
    settled_on DATE NOT NULL,
    price_aud  INTEGER NOT NULL,
    source_id  BIGINT NOT NULL REFERENCES source(id)
);

-- Asked vs settled: the latest asking price per lot next to its settlement.
CREATE VIEW asked_vs_settled AS
SELECT d.name AS development, d.suburb, d.lga, s.name AS stage, l.lot_no, l.property_type,
       po.price_aud AS last_asking_price, po.observed_on AS asked_on,
       st.price_aud AS settled_price, st.settled_on
FROM lot l
JOIN stage s ON s.id = l.stage_id
JOIN development d ON d.id = s.development_id
LEFT JOIN LATERAL (
    SELECT price_aud, observed_on FROM price_observation
    WHERE lot_id = l.id AND price_aud IS NOT NULL
    ORDER BY observed_on DESC LIMIT 1
) po ON TRUE
LEFT JOIN settlement st ON st.lot_id = l.id;
