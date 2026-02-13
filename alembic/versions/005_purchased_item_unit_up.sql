-- Rename purchased_item.quantity_unit to purchased_item.unit
-- and add purchased_item.unit_quantity DECIMAL(12, 3)

ALTER TABLE purchased_item
    RENAME COLUMN quantity_unit TO unit;

ALTER TABLE purchased_item
    ADD COLUMN unit_quantity DECIMAL(12, 3);
