-- FundPort Database Schema
-- Unified Fund Management Trading App

-- ============================================================
-- Users & Authentication
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- ============================================================
-- Broker Connections
-- ============================================================
CREATE TABLE IF NOT EXISTS broker_connections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    broker_type VARCHAR(50) NOT NULL DEFAULT 'paper',
    market_type ENUM('stocks', 'crypto', 'both') NOT NULL DEFAULT 'stocks',
    is_active BOOLEAN DEFAULT TRUE,
    config_json JSON DEFAULT NULL,
    sub_account_id VARCHAR(100),
    is_connected BOOLEAN DEFAULT FALSE,
    last_connected_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- Portfolios
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    broker_connection_id INT,

    -- Identity
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_currency VARCHAR(10) NOT NULL DEFAULT 'USD',

    -- Capital
    total_capital DECIMAL(15,2) NOT NULL DEFAULT 0.00,

    -- Status
    status ENUM('active', 'inactive', 'archived') DEFAULT 'active',

    -- Rebalance config (user-configurable in app/web)
    rebalance_method ENUM('weight_only', 'target_value', 'drift') DEFAULT 'weight_only',
    rebalance_order_type ENUM('market', 'limit') DEFAULT 'market',
    limit_price_tolerance_pct DECIMAL(5,2) DEFAULT 0.50,
    drift_threshold_pct DECIMAL(5,2) DEFAULT 5.00,
    cash_reserve_pct DECIMAL(5,2) DEFAULT 0.00,
    auto_rebalance_enabled BOOLEAN DEFAULT FALSE,
    rebalance_frequency VARCHAR(20) DEFAULT 'drift_only',

    -- Aggregated stats
    total_value DECIMAL(15,2) DEFAULT 0.00,
    total_cost DECIMAL(15,2) DEFAULT 0.00,
    total_pnl DECIMAL(15,2) DEFAULT 0.00,
    total_pnl_pct DECIMAL(7,4) DEFAULT 0.00,
    last_rebalanced_at TIMESTAMP NULL,
    last_synced_at TIMESTAMP NULL,

    -- Multi-account broker sub-account
    broker_sub_account_id VARCHAR(100),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (broker_connection_id) REFERENCES broker_connections(id) ON DELETE SET NULL,
    INDEX idx_portfolio_user (user_id)
);

-- ============================================================
-- Portfolio Holdings
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_holdings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,

    -- Identity
    symbol VARCHAR(20) NOT NULL,
    asset_type VARCHAR(20) DEFAULT 'stock',
    market VARCHAR(10) NOT NULL DEFAULT 'US',
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',

    -- Target
    target_weight_pct DECIMAL(7,4) NOT NULL,

    -- Current state
    current_shares DECIMAL(15,4) DEFAULT 0,
    avg_cost DECIMAL(15,4) DEFAULT 0,
    current_price DECIMAL(15,4) DEFAULT 0,
    market_value DECIMAL(15,2) DEFAULT 0,
    unrealized_pnl DECIMAL(15,2) DEFAULT 0,
    unrealized_pnl_pct DECIMAL(7,4) DEFAULT 0,

    -- Flags
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_portfolio_symbol (portfolio_id, symbol),
    INDEX idx_holding_portfolio (portfolio_id)
);

-- ============================================================
-- Rebalance Orders
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_rebalance_orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    user_id INT NOT NULL,

    -- Group tracking
    rebalance_group_id VARCHAR(36) NOT NULL,
    sequence INT DEFAULT 0,

    -- Order details
    symbol VARCHAR(20) NOT NULL,
    side ENUM('buy', 'sell') NOT NULL,
    order_type ENUM('market', 'limit') DEFAULT 'market',
    target_qty DECIMAL(15,4) NOT NULL,
    target_value DECIMAL(15,2) NOT NULL,
    limit_price DECIMAL(15,4),

    -- Execution
    status ENUM('pending', 'submitted', 'partially_filled', 'filled', 'cancelled', 'failed') DEFAULT 'pending',
    filled_qty DECIMAL(15,4) DEFAULT 0,
    avg_fill_price DECIMAL(15,4) DEFAULT 0,
    filled_value DECIMAL(15,2) DEFAULT 0,
    broker_order_id VARCHAR(100),

    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_rebalance_group (rebalance_group_id),
    INDEX idx_rebalance_portfolio (portfolio_id)
);

-- ============================================================
-- Performance Snapshots
-- ============================================================
CREATE TABLE IF NOT EXISTS portfolio_performance_snapshots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    snapshot_date DATE NOT NULL,

    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) DEFAULT 0,
    invested_value DECIMAL(15,2) DEFAULT 0,
    daily_pnl DECIMAL(15,2) DEFAULT 0,
    daily_return_pct DECIMAL(7,4) DEFAULT 0,
    total_pnl DECIMAL(15,2) DEFAULT 0,
    total_return_pct DECIMAL(7,4) DEFAULT 0,

    holdings_snapshot JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_snapshot (portfolio_id, snapshot_date)
);

-- ============================================================
-- Notifications / Alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    portfolio_id INT,
    type ENUM('rebalance', 'drift_alert', 'daily_report', 'error', 'system') NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    telegram_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE SET NULL
);

-- ============================================================
-- Default Admin User (password: admin123)
-- ============================================================
INSERT INTO users (username, email, password_hash, display_name, role) VALUES
('admin', 'admin@fundport.local', '$2b$12$LJ3m4ys3Lk0TSwHnbfOMiOXPm1Qlq5GzYxq5H8sK5x5x5x5x5x5x5x', 'Administrator', 'admin')
ON DUPLICATE KEY UPDATE username=username;
