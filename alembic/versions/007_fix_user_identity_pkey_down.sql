-- Revert user_identity table to use id as PRIMARY KEY

-- drop the composite PRIMARY KEY
ALTER TABLE user_identity DROP CONSTRAINT user_identity_pkey;

ALTER TABLE user_identity ADD PRIMARY KEY (id);

ALTER TABLE user_identity ADD CONSTRAINT user_identity_provider_id_key UNIQUE (provider, id);

