-- Change receipt.shop_id from UUID to INTEGER
-- Update all rows in the receipt table

DROP INDEX IF EXISTS idx_receipt_shop_id;

-- Alter the column type with USING clause to handle the conversion from UUID to INTEGER if there are any values
ALTER TABLE receipt 
ALTER COLUMN shop_id TYPE INTEGER USING (shop_id::text::integer);

-- Recreate the index
CREATE INDEX idx_receipt_shop_id ON receipt (shop_id);

DROP INDEX IF EXISTS idx_shop_item_shop_id;

ALTER TABLE shop_item
ALTER COLUMN shop_id TYPE INTEGER USING (shop_id::text::integer);

CREATE INDEX idx_shop_item_shop_id ON shop_item (shop_id);
