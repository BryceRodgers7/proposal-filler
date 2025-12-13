-- Migration 003: Add Organization Cards feature
-- This migration adds tables for organization cards and card actions (swipe likes/passes)

-- Create organization_cards table
CREATE TABLE IF NOT EXISTS organization_cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    subtitle TEXT,
    image_path VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Create indexes for organization_cards
CREATE INDEX IF NOT EXISTS idx_organization_cards_user_id ON organization_cards(user_id);
CREATE INDEX IF NOT EXISTS idx_organization_cards_is_deleted ON organization_cards(is_deleted);
CREATE INDEX IF NOT EXISTS idx_organization_cards_created_at ON organization_cards(created_at DESC);

-- Create card_actions table (similar to proposal_actions but for cards)
CREATE TABLE IF NOT EXISTS card_actions (
    id SERIAL PRIMARY KEY,
    card_id INTEGER NOT NULL REFERENCES organization_cards(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
    action_type VARCHAR(10) NOT NULL CHECK (action_type IN ('like', 'pass')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for card_actions
CREATE INDEX IF NOT EXISTS idx_card_actions_card_id ON card_actions(card_id);
CREATE INDEX IF NOT EXISTS idx_card_actions_user_id ON card_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_card_actions_action_type ON card_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_card_actions_created_at ON card_actions(created_at DESC);

-- Create unique constraint to prevent duplicate actions by same user on same card
CREATE UNIQUE INDEX IF NOT EXISTS idx_card_actions_unique_user_card ON card_actions(user_id, card_id);

