-- Chaves de idempotência para evitar tarefa NodeODM duplicada em retries.
-- O escopo é projeto + voo + usuário + chave; fingerprint diferente é conflito.
CREATE TABLE IF NOT EXISTS odm_idempotency_keys (
    id BIGSERIAL PRIMARY KEY,
    projeto_id BIGINT NOT NULL REFERENCES projetos(id) ON DELETE CASCADE,
    voo_id BIGINT NOT NULL REFERENCES voos(id) ON DELETE CASCADE,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    idempotency_key VARCHAR(128) NOT NULL,
    request_fingerprint CHAR(64) NOT NULL,
    odm_task_id VARCHAR(36) NOT NULL,
    processamento_id BIGINT REFERENCES processamentos_odm(id) ON DELETE SET NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_odm_idempotency_scope UNIQUE (projeto_id, voo_id, usuario_id, idempotency_key),
    CONSTRAINT uq_odm_idempotency_task UNIQUE (odm_task_id)
);

CREATE INDEX IF NOT EXISTS idx_odm_idempotency_processing
    ON odm_idempotency_keys(processamento_id);
