-- Run this in Supabase SQL editor

CREATE TYPE platform_enum AS ENUM ('instagram', 'telegram');
CREATE TYPE status_enum AS ENUM ('active', 'booked', 'dead', 'handed_off');

CREATE TABLE conversations (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    platform         platform_enum NOT NULL,
    user_id          TEXT NOT NULL,
    step             INTEGER NOT NULL DEFAULT 1,
    history          JSONB NOT NULL DEFAULT '[]',
    metadata         JSONB NOT NULL DEFAULT '{}',
    status           status_enum NOT NULL DEFAULT 'active',
    created_at       TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_message_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (platform, user_id)
);

CREATE TABLE corrections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context             TEXT NOT NULL,
    original_response   TEXT NOT NULL,
    corrected_response  TEXT NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE training_examples (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_message    TEXT NOT NULL,
    ideal_response  TEXT NOT NULL,
    notes           TEXT,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for performance
CREATE INDEX idx_conversations_platform_user
    ON conversations (platform, user_id);

CREATE INDEX idx_conversations_status
    ON conversations (status);

CREATE INDEX idx_conversations_last_message
    ON conversations (last_message_at);

-- Auto-update last_message_at on any row change
CREATE OR REPLACE FUNCTION update_last_message_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_message_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_update_timestamp
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_last_message_at();
