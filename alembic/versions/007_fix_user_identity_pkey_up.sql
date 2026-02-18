-- Fix user_identity table to use composite unique constraint on (id, provider)
-- instead of using id as PRIMARY KEY

ALTER TABLE user_identity DROP CONSTRAINT user_identity_pkey;

ALTER TABLE user_identity DROP CONSTRAINT IF EXISTS user_identity_provider_id_key;

-- add a composite PRIMARY KEY on (id, provider)
ALTER TABLE user_identity ADD PRIMARY KEY (id, provider);

