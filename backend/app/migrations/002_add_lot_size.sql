-- Migration: Add lot_size column to portfolio_holdings
-- For markets with minimum stock purchase units:
--   US   : 1 share (no lot restrictions)
--   HK   : varies per stock (default 100), e.g. HSBC=400, Tencent=100
--   CN   : 100 shares (A-shares round lot)
--   JP   : 100 shares (TSE standard lot)
--   CRYPTO: 1 (fractional units handled separately via market_config)

ALTER TABLE portfolio_holdings
    ADD COLUMN lot_size INTEGER NOT NULL DEFAULT 1
    COMMENT 'Minimum tradable unit: US=1, HK=lot (default 100), CN=100, JP=100';

-- Backfill lot_size for existing holdings based on market
-- US holdings: default 1 (already set by DEFAULT)
-- HK holdings: default 100 (override for known stocks set at app level)
-- CN holdings: 100
-- JP holdings: 100
-- CRYPTO holdings: 1 (already set by DEFAULT)

UPDATE portfolio_holdings
SET lot_size = 100
WHERE market IN ('HK', 'CN', 'JP');
