-- Downgrade for migration 006_receipt_shop_id_int is intentionally unsupported.
-- The shop_id columns were converted from UUID to INTEGER in the upgrade.
-- It is not possible to reliably reconstruct the original UUID values from the
-- stored INTEGERs, so an automatic downgrade would either fail or corrupt data.

DO $$
BEGIN
    RAISE EXCEPTION
        'Downgrade for migration 006_receipt_shop_id_int is not supported: cannot '
        'safely convert INTEGER shop_id values back to their original UUIDs.';
END;
$$;
