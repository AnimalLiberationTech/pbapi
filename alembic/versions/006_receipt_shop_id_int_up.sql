-- Change receipt.shop_id from UUID to INTEGER
-- Update all rows in the receipt table

DROP INDEX IF EXISTS idx_receipt_shop_id;

-- Ensure there are no non-NULL values before changing type; UUIDs cannot be safely cast to INTEGER
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM receipt WHERE shop_id IS NOT NULL) THEN
        RAISE EXCEPTION 'Migration aborted: receipt.shop_id contains non-NULL values that cannot be safely converted from UUID to INTEGER.';
    END IF;
END
$$;

-- Alter the column type; safe because any existing values are NULL
ALTER TABLE receipt
ALTER COLUMN shop_id TYPE INTEGER USING shop_id;

-- Recreate the index
CREATE INDEX idx_receipt_shop_id ON receipt (shop_id);

DROP INDEX IF EXISTS idx_shop_item_shop_id;

-- Ensure there are no non-NULL values before changing type; UUIDs cannot be safely cast to INTEGER
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM shop_item WHERE shop_id IS NOT NULL) THEN
        RAISE EXCEPTION 'Migration aborted: shop_item.shop_id contains non-NULL values that cannot be safely converted from UUID to INTEGER.';
    END IF;
END
$$;

-- Alter the column type; safe because any existing values are NULL
ALTER TABLE shop_item
ALTER COLUMN shop_id TYPE INTEGER USING shop_id;

CREATE INDEX idx_shop_item_shop_id ON shop_item (shop_id);
