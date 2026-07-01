-- ============================================================
-- AI Managers — LLM-powered portfolio managers for the Arena
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_managers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    org_id INT NOT NULL,
    user_id INT NOT NULL,

    -- Identity
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- LLM Configuration
    model_provider VARCHAR(50) NOT NULL DEFAULT 'opencode-go',
    model_name VARCHAR(100) NOT NULL,
    api_base_url VARCHAR(255),
    system_prompt TEXT,
    temperature DECIMAL(3,2) DEFAULT 0.70,
    max_tokens INT DEFAULT 4000,

    -- Portfolio link
    assigned_portfolio_id INT,

    -- Schedule
    run_frequency VARCHAR(20) DEFAULT 'daily',
    auto_run_enabled BOOLEAN DEFAULT FALSE,

    -- Cached performance stats
    total_return_pct DECIMAL(7,4) DEFAULT 0.0000,
    sharpe_ratio DECIMAL(7,4) DEFAULT 0.0000,
    win_rate DECIMAL(5,2) DEFAULT 0.00,
    total_trades INT DEFAULT 0,
    decisions_count INT DEFAULT 0,
    last_decision_at TIMESTAMP NULL,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_portfolio_id) REFERENCES portfolios(id) ON DELETE SET NULL,
    INDEX idx_ai_manager_org (org_id),
    INDEX idx_ai_manager_user (user_id)
);

-- ============================================================
-- AI Decision Logs — Full audit trail of every AI decision
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_decision_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ai_manager_id INT NOT NULL,
    portfolio_id INT,
    org_id INT NOT NULL,
    user_id INT NOT NULL,

    -- Trigger info
    triggered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    market_regime VARCHAR(20),
    trigger_source VARCHAR(20) DEFAULT 'manual',

    -- Full data context
    data_snapshot JSON,
    rag_results_used JSON,

    -- LLM interaction
    prompt_sent TEXT,
    raw_response TEXT,
    parsed_decision JSON,
    reasoning TEXT,

    -- Risk & benchmark
    risk_assessment JSON,
    benchmark_analysis JSON,

    -- Portfolio state
    portfolio_snapshot_before JSON,
    portfolio_snapshot_after JSON,

    -- Execution
    orders_created INT DEFAULT 0,
    execution_status VARCHAR(20) DEFAULT 'pending',
    execution_error TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ai_manager_id) REFERENCES ai_managers(id) ON DELETE CASCADE,
    FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE SET NULL,
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_decision_ai_manager (ai_manager_id),
    INDEX idx_decision_portfolio (portfolio_id),
    INDEX idx_decision_org (org_id),
    INDEX idx_decision_triggered (triggered_at)
);
