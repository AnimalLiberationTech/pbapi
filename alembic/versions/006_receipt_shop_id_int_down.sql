-- Revert receipt.shop_id from INTEGER to UUID
DROP INDEX IF EXISTS idx_receipt_shop_id;

ALTER TABLE receipt 
ALTER COLUMN shop_id TYPE UUID USING (shop_id::text::uuid);

CREATE INDEX idx_receipt_shop_id ON receipt (shop_id);

-- Revert shop_item.shop_id from INTEGER to UUID
DROP INDEX IF EXISTS idx_shop_item_shop_id;

ALTER TABLE shop_item
ALTER COLUMN shop_id TYPE UUID USING (shop_id::text::uuid);

CREATE INDEX idx_shop_item_shop_id ON shop_item (shop_id);
