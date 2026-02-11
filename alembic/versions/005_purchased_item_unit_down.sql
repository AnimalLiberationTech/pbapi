-- Revert changes: rename purchased_item.unit back to purchased_item.quantity_unit
-- and drop purchased_item.unit_quantity column

ALTER TABLE purchased_item
    RENAME COLUMN unit TO quantity_unit;

ALTER TABLE purchased_item
    DROP COLUMN unit_quantity;
