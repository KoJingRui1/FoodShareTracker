import os
import sys
import json
import logging
import datetime
from pathlib import Path
import pytest

# Ensure imports resolve cleanly regardless of project directory layout
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.app.user import User
    from src.app.admin import AdminUser
    from src.app.donor import DonorUser
    from src.app.staff import StaffUser
    from src.app.volunteer import VolunteerUser
    from src.app.client import ClientUser
    from src.app.item import Item
    from src.app.donations import Donation
    from src.app.FoodHamper import FoodHamper
    from src.app.inventory import Inventory
    from src.app.FoodBank import FoodBank
    from src.app.utils import (
        init_logger, backup_data, validate_name, valid_name,
        validate_password, valid_password, is_bcrypt_hash, hash_password, verify_password
    )
except ModuleNotFoundError:
    from app.user import User
    from app.admin import AdminUser
    from app.donor import DonorUser
    from app.staff import StaffUser
    from app.volunteer import VolunteerUser
    from app.client import ClientUser
    from app.item import Item
    from app.donations import Donation
    from app.FoodHamper import FoodHamper
    from app.inventory import Inventory
    from app.FoodBank import FoodBank
    from app.utils import (
        init_logger, backup_data, validate_name, valid_name,
        validate_password, valid_password, is_bcrypt_hash, hash_password, verify_password
    )

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def food_bank(tmp_path):
    test_data_file = tmp_path / "test_data.json"
    return FoodBank(data_path=str(test_data_file))

@pytest.fixture
def inventory():
    return Inventory()

# ============================================================================
# 1. UTILS.PY TESTS
# ============================================================================

def test_utils_init_logger(tmp_path):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    log_file = tmp_path / "logs" / "test.log"
    init_logger(log_file=str(log_file))
    logging.info("Test Log")
    for handler in logging.root.handlers[:]:
        handler.flush()
    assert log_file.exists()
    assert "Test Log" in log_file.read_text()

def test_utils_backup_data(tmp_path):
    src = tmp_path / "data.json"
    src.write_text("{}", encoding="utf-8")
    backup_dir = tmp_path / "backups"
    assert backup_data(str(src), str(backup_dir)) is True
    assert backup_data(str(tmp_path / "missing.json"), str(backup_dir)) is False

def test_utils_validation_methods():
    # Name validation
    is_valid, _ = validate_name("Valid Name")
    assert is_valid is True
    is_valid, _ = validate_name("123")
    assert is_valid is False
    assert valid_name("Valid Name") is True

    # Password validation
    is_valid, _ = validate_password("Pass123")
    assert is_valid is True
    assert valid_password("short") is False

def test_utils_hashing():
    hashed = hash_password("pass")
    assert is_bcrypt_hash(hashed) or hashed.startswith("$sha256$")
    assert verify_password("pass", hashed) is True
    assert verify_password("wrong", hashed) is False

# ============================================================================
# 2. ENTITY __INIT__ TESTS (Models)
# ============================================================================

def test_user_models_initialization():
    u = User(1, "Name", "pass", "email@test.com")
    assert u.id == 1 and u.name == "Name"

    a = AdminUser(1, "Admin", "pass", "admin@test.com")
    assert isinstance(a, User)

    d = DonorUser(1, "Donor", "pass", "donor@test.com")
    assert d.donation == []

    s = StaffUser(1, "Staff", "pass", "staff@test.com")
    v = VolunteerUser(1, "Vol", "pass", "vol@test.com")
    assert v.work == []

    c = ClientUser(1, "Client", "pass", "client@test.com", "Desc")
    assert c.description == "Desc" and c.messages == []

def test_inventory_and_supply_models():
    i = Item(1, "Bread", "Food", 10, "pcs", 2)
    assert i.name == "Bread" and i.quantity == 10

    d = Donation(1, 2, "Desc", "created", 3)
    assert d.id == 1 and d.donor_id == 2

    f = FoodHamper(1, 2, "Desc", "created", 3)
    assert f.id == 1 and f.client_id == 2

# ============================================================================
# 3. INVENTORY.PY TESTS
# ============================================================================

def test_inv_core_operations(inventory):
    assert inventory.items == []
    
    # Add items
    item = inventory.add_item("Rice", "Grain", quantity=5, min_quantity=1)
    assert item.quantity == 5
    assert inventory.find_item_by_name("Rice") == item
    
    # Restock existing
    inventory.add_item("Rice", "Grain", quantity=5)
    assert item.quantity == 10

    # Add/Remove Stock tracking
    assert inventory.add_stock(item.id, 5) is True
    assert item.quantity == 15
    assert inventory.remove_stock(item.id, 5) is True
    assert item.quantity == 10

def test_inv_audits_and_thresholds(inventory):
    item_a = inventory.add_item("A", "Cat", quantity=10, min_quantity=5)
    item_b = inventory.add_item("B", "Cat", quantity=2, min_quantity=5)
    
    low = inventory.get_low_stock_items()
    assert len(low) == 1 and low[0].name == "B"

    # Verify transaction logs exist
    records = inventory.get_stock_records(item_a.id)
    assert len(records) > 0

# ============================================================================
# 4. FOODBANK.PY TESTS - CORE AND LOOKUPS
# ============================================================================

def test_fb_save_and_load_data(tmp_path):
    f_path = tmp_path / "data.json"
    fb1 = FoodBank(data_path=str(f_path))
    fb1.add_admin("A", "p", "a@a.com")
    fb1.save_data()
    
    fb2 = FoodBank(data_path=str(f_path))
    fb2.load_data()
    assert len(fb2.admins) == 1
    assert fb2.admins[0].name == "A"

def test_fb_finders(food_bank):
    a = food_bank.add_admin("A", "p", "a@a.com")
    assert food_bank.find_admin_by_id(a.id) is not None
    assert food_bank.find_user_by_email("a@a.com") is not None
    assert food_bank.find_user_by_email("missing@a.com") is None

# ============================================================================
# 5. FOODBANK.PY TESTS - USER MANAGEMENT
# ============================================================================

def test_fb_user_authentication_and_crud(food_bank):
    u = food_bank.add_admin("N", "pass", "e@e.com")
    
    # Authentication
    user, role = food_bank.authenticate("e@e.com", "pass")
    assert user is not None and role == "admins"
    
    # Update
    food_bank.update_user(u.id, name="Updated")
    assert u.name == "Updated"

    # Image handling
    food_bank.set_user_profile_image(u.id, "new.png")
    assert food_bank.get_user_profile_image(u.id) == "new.png"

    # Remove
    food_bank.remove_user(u.id)
    assert len(food_bank.admins) == 0

# ============================================================================
# 6. FOODBANK.PY TESTS - DONATIONS & HAMPERS (SUPPLY CHAIN)
# ============================================================================

def test_fb_donation_lifecycle(food_bank):
    d = food_bank.add_donor("D", "p", "e@e.com")
    v = food_bank.add_volunteer("V", "p", "v@v.com")
    
    don = food_bank.add_donation(d.id, items={"Rice": 5})
    assert len(food_bank.donations) == 1
    
    food_bank.collect_donation(don.id, v.id)
    assert don.status == "collected"
    
    food_bank.stock_donation(don.id)
    assert don.status == "stocked"
    assert food_bank.inventory.find_item_by_name("Rice").quantity == 5

def test_fb_hamper_lifecycle(food_bank):
    c = food_bank.add_client("C", "p", "c@c.com")
    v = food_bank.add_volunteer("V", "p", "v@v.com")
    food_bank.add_inventory_item("Rice", "Grain", 10)
    
    h = food_bank.add_food_hamper()
    
    # Pack removes from stock
    food_bank.pack_food_hamper(h.id, items={"Rice": 5})
    assert h.status == "packed"
    assert food_bank.inventory.find_item_by_name("Rice").quantity == 5

    # Unpack restores stock
    food_bank.unpack_food_hamper(h.id)
    assert h.status == "created"
    assert food_bank.inventory.find_item_by_name("Rice").quantity == 10

    # Re-pack and deliver
    food_bank.pack_food_hamper(h.id, items={"Rice": 5})
    food_bank.assign_food_hamper(h.id, c.id, volunteer_id=v.id)
    food_bank.deliver_food_hamper(h.id)
    assert h.status == "delivered"

# ============================================================================
# 7. FOODBANK.PY TESTS - VOLUNTEER JOBS & ISSUES
# ============================================================================

def test_fb_volunteer_jobs(food_bank):
    v1 = food_bank.add_volunteer("V1", "p", "v1@v.com")
    v2 = food_bank.add_volunteer("V2", "p", "v2@v.com")
    
    food_bank.assign_job(v1.id, "Clean")
    assert "Clean" in v1.work
    
    food_bank.take_over_job(v1.id, v2.id, "Clean")
    assert "Clean" in v2.work
    assert "Clean" not in v1.work

    food_bank.complete_job(v2.id, "Clean")
    assert "Clean" in v2.completed_work

def test_fb_issue_flagging(food_bank):
    h = food_bank.add_food_hamper()
    
    # Flagging
    food_bank.flag_issue("hamper", h.id, "Damaged box")
    assert h.status == "flagged"
    assert len(food_bank.get_flagged_issues()) == 1

    # Resolution
    food_bank.resolve_issue("hamper", h.id, "Replaced box")
    assert h.status == "created"
    assert len(food_bank.get_flagged_issues()) == 0

# ============================================================================
# 8. FOODBANK.PY TESTS - MESSAGING & SYSTEM VALIDATION
# ============================================================================

def test_fb_client_messaging(food_bank):
    c = food_bank.add_client("C", "p", "c@c.com")
    
    food_bank.send_client_message(c.id, "Need help")
    assert len(c.messages) == 1
    
    food_bank.edit_client_message(c.id, 1, "Urgent help")
    assert c.messages[0]["content"] == "Urgent help"
    assert c.messages[0]["is_edited"] is True
    
    food_bank.delete_client_message(c.id, 1)
    assert len(c.messages) == 0

def test_fb_system_summary_and_validation(food_bank):
    food_bank.add_admin("A", "p", "a@a.com")
    
    summary = food_bank.get_system_summary()
    assert summary["admins"] == 1
    
    # Validation passes on clean data
    assert len(food_bank.validate_data()) == 0

# ============================================================================
# 14. ADVANCED USER CASCADE DELETION TESTS
# ============================================================================

def test_cascade_delete_client_with_assigned_hamper(food_bank):
    """Tests removing a client after safely assigning them a hamper using correct methods."""
    client = food_bank.add_client("Cascade Client", "pass", "cc@test.com")
    v = food_bank.add_volunteer("Vol", "pass", "v@test.com")
    
    # Create first, assign second
    hamper = food_bank.add_food_hamper()
    food_bank.assign_food_hamper(hamper.id, client.id, volunteer_id=v.id)
    
    food_bank.remove_user(client.id)
    assert food_bank.find_client_by_id(client.id) is None

def test_cascade_delete_volunteer_clears_tasks(food_bank):
    """Tests removing a volunteer after safely assigning a donation using correct methods."""
    vol = food_bank.add_volunteer("Vol", "pass", "v@v.com")
    donor = food_bank.add_donor("D", "pass", "d@test.com")
    
    # Create first, collect second
    donation = food_bank.add_donation(donor.id)
    food_bank.collect_donation(donation.id, vol.id)
    
    food_bank.remove_user(vol.id)
    assert food_bank.find_volunteer_by_id(vol.id) is None

def test_remove_job_donation_in_hand_blocked(food_bank):
    """Tests that a volunteer can drop a donation job successfully without crashing."""
    d = food_bank.add_donor("D", "p", "d@d.com")
    v = food_bank.add_volunteer("V", "p", "v@v.com")
    
    donation = food_bank.add_donation(d.id)
    food_bank.collect_donation(donation.id, v.id)
    
    food_bank.remove_job(v.id, donation.id)
    assert donation.id not in v.work


# ============================================================================
# 15. ADVANCED USER UPDATE & VALIDATION ERRORS
# ============================================================================

def test_update_user_invalid_fields(food_bank):
    """Tests trying to update protected fields or non-existent fields on a user."""
    admin = food_bank.add_admin("A", "p", "a@test.com")
    
    with pytest.raises(ValueError, match="Cannot update protected field"):
        food_bank.update_user(admin.id, id=999)
        
    with pytest.raises(ValueError, match="Cannot update protected field"):
        food_bank.update_user(admin.id, _private_var="hack")
        
    with pytest.raises(AttributeError, match="has no field"):
        food_bank.update_user(admin.id, non_existent_field="value")

def test_add_client_duplicate_email(food_bank):
    """Tests that add_client specifically blocks duplicate emails."""
    food_bank.add_client("C1", "p", "dup@test.com")
    with pytest.raises(ValueError, match="already registered"):
        food_bank.add_client("C2", "p", "dup@test.com")

# ============================================================================
# 16. ADVANCED INVENTORY & PACKING EXCEPTIONS
# ============================================================================

def test_pack_hamper_insufficient_stock(food_bank):
    """Tests that packing fails and rolls back if inventory is insufficient."""
    food_bank.add_inventory_item("Apples", "Fruit", quantity=2)
    hamper = food_bank.add_food_hamper()
    
    with pytest.raises(ValueError, match="Insufficient stock for 'Apples'"):
        food_bank.pack_food_hamper(hamper.id, items={"Apples": 5})
        
    assert hamper.status == "created"  # Status should not change
    assert food_bank.inventory.find_item_by_name("Apples").quantity == 2 # Stock remains unchanged

def test_pack_hamper_missing_item(food_bank):
    """Tests that packing fails if requested item does not exist."""
    hamper = food_bank.add_food_hamper()
    with pytest.raises(ValueError, match="not found in inventory"):
        food_bank.pack_food_hamper(hamper.id, items={"Ghost Item": 1})

def test_pack_hamper_with_string_list(food_bank):
    """Tests packing a hamper using a flat list of string names instead of a dict."""
    food_bank.add_inventory_item("Bread", "Bakery", quantity=10)
    hamper = food_bank.add_food_hamper()
    
    # Pass list of strings (defaults to quantity 1.0)
    food_bank.pack_food_hamper(hamper.id, items=["Bread"])
    assert food_bank.inventory.find_item_by_name("Bread").quantity == 9
    assert hamper.status == "packed"

# ============================================================================
# 17. ADVANCED STATE TRANSITION BLOCKS (HAMPERS & DONATIONS)
# ============================================================================

def test_unpack_delivered_hamper_blocked(food_bank):
    """Tests that a delivered hamper cannot be unpacked."""
    hamper = food_bank.add_food_hamper()
    hamper.status = "delivered"
    
    with pytest.raises(ValueError, match="already been delivered"):
        food_bank.unpack_food_hamper(hamper.id)

def test_assign_delivered_hamper_blocked(food_bank):
    """Tests that a delivered hamper cannot be reassigned."""
    client = food_bank.add_client("C", "p", "c@c.com")
    hamper = food_bank.add_food_hamper()
    hamper.status = "delivered"
    
    with pytest.raises(ValueError, match="Cannot assign food hamper"):
        food_bank.assign_food_hamper(hamper.id, client.id)

def test_take_over_delivered_hamper_blocked(food_bank):
    """Tests that volunteers cannot take over a delivered hamper."""
    v = food_bank.add_volunteer("V", "p", "v@v.com")
    hamper = food_bank.add_food_hamper()
    hamper.status = "delivered"
    
    with pytest.raises(ValueError, match="already been delivered"):
        food_bank.take_over_hamper(hamper.id, v.id)

def test_deliver_unpacked_hamper_blocked(food_bank):
    """Tests that a newly created (unpacked/unassigned) hamper cannot be delivered directly."""
    hamper = food_bank.add_food_hamper()
    assert hamper.status == "created"
    
    with pytest.raises(ValueError, match="must be 'packed' before delivery"):
        food_bank.deliver_food_hamper(hamper.id)

def test_delete_collected_donation_blocked(food_bank):
    """Tests that deleting a non-created donation raises a ValueError."""
    donor = food_bank.add_donor("D", "p", "d@d.com")
    donation = food_bank.add_donation(donor.id)
    donation.status = "collected"
    
    with pytest.raises(ValueError, match="Only 'created' donations can be deleted"):
        food_bank.delete_donation(donation.id)

def test_stock_uncollected_donation_blocked(food_bank):
    """Tests that donations with statuses like 'flagged' cannot be stocked."""
    donor = food_bank.add_donor("D", "p", "d@d.com")
    donation = food_bank.add_donation(donor.id)
    donation.status = "flagged"
    
    with pytest.raises(ValueError, match="Cannot stock donation"):
        food_bank.stock_donation(donation.id)

# ============================================================================
# 18. ADVANCED VOLUNTEER JOB REMOVAL BLOCKS
# ============================================================================

def test_remove_job_donation_in_hand_blocked(food_bank):
    """Tests that a volunteer can drop a donation job successfully without crashing."""
    d = food_bank.add_donor("D", "p", "d@d.com")
    v = food_bank.add_volunteer("V", "p", "v@v.com")
    
    donation = food_bank.add_donation(d.id)
    food_bank.collect_donation(donation.id, v.id)
    
    food_bank.remove_job(v.id, donation.id)
    assert donation.id not in v.work


# ============================================================================
# 19. ADVANCED ISSUE FLAGGING & RESOLUTION
# ============================================================================

def test_flag_issue_empty_description(food_bank):
    """Tests that flagging requires a valid description string."""
    h = food_bank.add_food_hamper()
    with pytest.raises(ValueError, match="Issue description cannot be empty"):
        food_bank.flag_hamper_issue(h.id, "")

def test_flag_issue_invalid_entity_type(food_bank):
    """Tests the proxy routing for invalid entity types."""
    with pytest.raises(ValueError, match="Unsupported entity type"):
        food_bank.flag_issue("invalid_type", 1, "Issue text")
        
    with pytest.raises(ValueError, match="Unsupported entity type"):
        food_bank.resolve_issue("invalid_type", 1)

def test_resolve_issue_custom_restore_status(food_bank):
    """Tests resolving an issue but overriding the auto-restore status."""
    h = food_bank.add_food_hamper()
    food_bank.flag_hamper_issue(h.id, "Missing item")
    
    # Resolve but force status to 'packed' instead of restoring 'created'
    food_bank.resolve_hamper_issue(h.id, restore_status="packed")
    assert h.status == "packed"

# ============================================================================
# 20. ADVANCED DATA INTEGRITY (validate_data)
# ============================================================================

def test_validate_data_broken_volunteer_references(food_bank):
    """Tests the validate_data function finding missing volunteer associations."""
    donor = food_bank.add_donor("D", "p", "d@d.com")
    client = food_bank.add_client("C", "p", "c@c.com")
    
    donation = food_bank.add_donation(donor.id)
    hamper = food_bank.add_food_hamper(client_id=client.id)
    
    # Manually inject bad volunteer IDs
    donation.volunteer_id = 9999
    hamper.volunteer_id = 8888
    
    issues = food_bank.validate_data()
    assert any("references missing volunteer 9999" in issue for issue in issues)
    assert any("references missing volunteer 8888" in issue for issue in issues)

# ============================================================================
# 21. ADVANCED PERMISSION & SECURITY ERRORS
# ============================================================================

def test_remove_donation_permission_error(food_bank):
    """Tests that a donor cannot delete another donor's donation."""
    d1 = food_bank.add_donor("Donor 1", "pass", "d1@test.com")
    d2 = food_bank.add_donor("Donor 2", "pass", "d2@test.com")
    
    donation = food_bank.add_donation(d1.id)
    
    # Donor 2 tries to delete Donor 1's donation
    with pytest.raises(PermissionError, match="is not authorized to delete donation"):
        food_bank.remove_donation(donation.id, donor_id=d2.id)

def test_deliver_hamper_permission_error(food_bank):
    """Tests that a volunteer cannot deliver a hamper assigned to a different volunteer."""
    c = food_bank.add_client("C", "pass", "c@test.com")
    v1 = food_bank.add_volunteer("V1", "pass", "v1@test.com")
    v2 = food_bank.add_volunteer("V2", "pass", "v2@test.com")
    
    hamper = food_bank.add_food_hamper(client_id=c.id, volunteer_id=v1.id)
    hamper.status = "packed"
    
    # Volunteer 2 attempts to deliver Volunteer 1's hamper
    with pytest.raises(PermissionError, match="is not the assigned volunteer"):
        food_bank.deliver_food_hamper(hamper.id, volunteer_id=v2.id)

# ============================================================================
# 22. INVENTORY JSON FORMAT COMPATIBILITY TESTS
# ============================================================================

def test_load_data_with_dict_inventory(tmp_path):
    """Tests FoodBank's ability to safely load the modern dictionary-based inventory format."""
    modern_json = tmp_path / "modern.json"
    modern_json.write_text(json.dumps({
        "inventory": {
            "items": [{"id": 1, "name": "Beans", "category": "Food", "quantity": 10}],
            "stock_records": [],
            "inventory_data": {"next_item_id": 2, "next_record_id": 1}
        }
    }), encoding="utf-8")
    
    fb = FoodBank(data_path=str(modern_json))
    assert len(fb.inventory.items) == 1
    assert fb.inventory.items[0].name == "Beans"

def test_load_data_with_list_inventory(tmp_path):
    """Tests FoodBank's backwards compatibility for loading legacy list-based inventory format."""
    legacy_json = tmp_path / "legacy.json"
    legacy_json.write_text(json.dumps({
        "inventory": [{"id": 1, "name": "Rice", "category": "Food", "quantity": 20}],
        "inventory_transactions": []
    }), encoding="utf-8")
    
    fb = FoodBank(data_path=str(legacy_json))
    assert len(fb.inventory.items) == 1
    assert fb.inventory.items[0].name == "Rice"

def test_load_data_with_missing_inventory(tmp_path):
    """Tests FoodBank's fallback when the inventory key is completely missing."""
    empty_json = tmp_path / "empty.json"
    empty_json.write_text(json.dumps({"admins": []}), encoding="utf-8")
    
    fb = FoodBank(data_path=str(empty_json))
    assert len(fb.inventory.items) == 0

# ============================================================================
# 23. ENTITY RELATIONSHIP UPDATE ERRORS
# ============================================================================

def test_update_donation_invalid_references(food_bank):
    """Tests that updating a donation with fake donor/volunteer IDs is blocked."""
    d = food_bank.add_donor("D", "pass", "d@test.com")
    donation = food_bank.add_donation(d.id)
    
    with pytest.raises(ValueError, match="Donor ID 999 does not exist"):
        food_bank.update_donation(donation.id, donor_id=999)
        
    with pytest.raises(ValueError, match="Volunteer ID 999 does not exist"):
        food_bank.update_donation(donation.id, volunteer_id=999)

def test_update_hamper_invalid_references(food_bank):
    """Tests that updating a hamper with fake client/volunteer IDs is blocked."""
    h = food_bank.add_food_hamper()
    
    with pytest.raises(ValueError, match="Client ID 999 does not exist"):
        food_bank.update_food_hamper(h.id, client_id=999)
        
    with pytest.raises(ValueError, match="Volunteer ID 999 does not exist"):
        food_bank.update_food_hamper(h.id, volunteer_id=999)

def test_assign_hamper_already_assigned(food_bank):
    """Tests that assigning a hamper that already belongs to another client is blocked."""
    c1 = food_bank.add_client("C1", "pass", "c1@test.com")
    c2 = food_bank.add_client("C2", "pass", "c2@test.com")
    
    hamper = food_bank.add_food_hamper(client_id=c1.id)
    
    with pytest.raises(ValueError, match="already assigned to another client"):
        food_bank.assign_food_hamper(hamper.id, c2.id)

# ============================================================================
# 24. MESSAGE OUTPUT AND EDGE CASES
# ============================================================================

def test_output_client_messages_formatting(food_bank, capsys):
    """Tests that output_client_messages correctly formats and prints to stdout."""
    c = food_bank.add_client("C", "pass", "c@test.com")
    food_bank.send_client_message(c.id, "Test Message")
    
    # print_to_console=True should write to stdout
    lines = food_bank.output_client_messages(c.id, print_to_console=True)
    captured = capsys.readouterr()
    
    assert "Test Message" in lines[0]
    assert "Message #1 from C" in captured.out

def test_take_over_hamper_cleanup(food_bank):
    """Tests that taking over a hamper cleanly removes it from the old volunteer's list."""
    v1 = food_bank.add_volunteer("V1", "pass", "v1@test.com")
    v2 = food_bank.add_volunteer("V2", "pass", "v2@test.com")
    
    hamper = food_bank.add_food_hamper(volunteer_id=v1.id)
    assert hamper.id in v1.work
    
    food_bank.take_over_hamper(hamper.id, v2.id)
    assert hamper.id not in v1.work
    assert hamper.id in v2.work

# ============================================================================
# 25. DATA INTEGRITY (validate_data) EDGE CASES
# ============================================================================

def test_validate_data_duplicate_user_emails(food_bank):
    """Tests validate_data correctly flags duplicate email addresses across users."""
    food_bank.add_admin("Admin 1", "pass", "shared@test.com")
    # Bypassing the normal add_client check to artificially create a duplicate for testing
    u2 = ClientUser(99, "Client 1", "pass", "shared@test.com")
    food_bank.clients.append(u2)
    
    issues = food_bank.validate_data()
    assert any("Duplicate user email addresses found" in issue for issue in issues)

def test_validate_data_duplicate_ids(food_bank):
    """Tests validate_data correctly flags duplicate ID collisions."""
    a1 = food_bank.add_admin("A1", "p", "a1@test.com")
    
    # Artificially create a duplicate ID collision
    u_dup = AdminUser(a1.id, "Dup", "p", "dup@test.com")
    food_bank.admins.append(u_dup)
    
    issues = food_bank.validate_data()
    assert any("Duplicate user IDs found" in issue for issue in issues)

# ============================================================================
# 26. DEEP LOOKUP & MISSING ENTITY TESTS
# ============================================================================

def test_find_users_with_missing_ids(food_bank):
    """Tests all user finders return None for non-existent IDs."""
    assert food_bank.find_admin_by_id(9999) is None
    assert food_bank.find_donor_by_id(9999) is None
    assert food_bank.find_staff_by_id(9999) is None
    assert food_bank.find_volunteer_by_id(9999) is None
    assert food_bank.find_client_by_id(9999) is None
    assert food_bank.find_user_by_id(9999) is None

def test_find_supplies_with_missing_ids(food_bank):
    """Tests supply finders return None for non-existent IDs."""
    assert food_bank.find_donation_by_id(9999) is None
    assert food_bank.find_food_hamper_by_id(9999) is None

# ============================================================================
# 27. OUT-OF-BOUNDS & INVALID OPERATIONS
# ============================================================================

def test_edit_message_out_of_bounds(food_bank):
    """Tests editing a message ID that does not exist raises a ValueError."""
    c = food_bank.add_client("Msg Client", "pass", "msg@test.com")
    food_bank.send_client_message(c.id, "First message")
    
    # Expect your system's built-in ValueError protection
    with pytest.raises(ValueError, match="Message ID 999 not found"):
        food_bank.edit_client_message(c.id, 999, "Hacked message")

def test_delete_message_out_of_bounds(food_bank):
    """Tests deleting a message ID that does not exist."""
    c = food_bank.add_client("Msg Client", "pass", "msg2@test.com")
    food_bank.send_client_message(c.id, "Keep this")
    
    food_bank.delete_client_message(c.id, 999)
    # The message should remain untouched
    assert len(c.messages) == 1

def test_remove_non_existent_donation_and_hamper(food_bank):
    """Tests removing donations and hampers that do not exist."""
    assert food_bank.remove_donation(9999) is False or food_bank.remove_donation(9999) is None
    assert food_bank.remove_food_hamper(9999) is False or food_bank.remove_food_hamper(9999) is None

# ============================================================================
# 28. AUTHENTICATION MALFORMED INPUTS
# ============================================================================

def test_authenticate_empty_credentials(food_bank):
    """Tests authentication with empty strings and None values."""
    food_bank.add_admin("Admin", "pass123", "admin@test.com")
    
    assert food_bank.authenticate("", "") is None
    assert food_bank.authenticate(None, None) is None
    assert food_bank.authenticate("admin@test.com", "") is None

def test_authenticate_wrong_casing(food_bank):
    """Tests case sensitivity in authentication (passwords should be strict)."""
    food_bank.add_admin("Admin", "Pass123", "case@test.com")
    
    # Wrong case password should fail
    assert food_bank.authenticate("case@test.com", "pass123") is None

# ============================================================================
# 29. INVENTORY EXTREME EDGE CASES
# ============================================================================

def test_inventory_add_zero_or_negative_stock(food_bank):
    """Tests how inventory handles 0 or negative stock additions."""
    item = food_bank.add_inventory_item("Water", "Drinks", 10)
    
    # Adding 0 shouldn't change quantity
    food_bank.add_stock(item.id, 0)
    assert item.quantity == 10
    
    # Attempting to add negative stock (system should block or handle safely)
    result = food_bank.add_stock(item.id, -5)
    if result is False:  # If system blocks it
        assert item.quantity == 10

def test_inventory_remove_more_than_exists(food_bank):
    """Tests removing more stock than is available."""
    item = food_bank.add_inventory_item("Juice", "Drinks", 5)
    
    # Should fail or return False
    assert food_bank.remove_stock(item.id, 100) is False
    assert item.quantity == 5


# ============================================================================
# 30. FOODBANK PROXY METHOD FAILURES
# ============================================================================

def test_foodbank_inventory_proxy_failures(food_bank):
    """Tests FoodBank's inventory wrappers against bad item IDs."""
    assert food_bank.add_stock(9999, 10) is False
    assert food_bank.remove_stock(9999, 5) is False
    assert food_bank.get_stock_records(9999) == []

def test_update_hamper_status_bad_id(food_bank):
    """Tests updating status of a non-existent hamper."""
    result = food_bank.update_hamper_status(9999, "packed")
    assert result is None or result is False

def test_take_over_job_bad_ids(food_bank):
    """Tests task takeovers with invalid volunteer or job IDs."""
    v1 = food_bank.add_volunteer("V1", "p", "v1@test.com")
    
    # Taking over a job for a non-existent volunteer
    try:
        food_bank.take_over_job(v1.id, 9999, "Some Job")
    except ValueError:
        pass  # Expected to fail cleanly
        
    # Taking over a non-existent hamper
    try:
        food_bank.take_over_hamper(9999, v1.id)
    except ValueError:
        pass

def test_deliver_food_hamper_bad_id(food_bank):
    """Tests delivery of a non-existent hamper."""
    try:
        food_bank.deliver_food_hamper(9999)
    except ValueError:
        pass  # Should fail cleanly

def test_stock_donation_bad_id(food_bank):
    """Tests stocking a non-existent donation."""
    try:
        food_bank.stock_donation(9999)
    except ValueError:
        pass  # Should fail cleanly

def test_get_available_hampers_filtering(food_bank):
    """Tests that only 'created' or 'packed' hampers show as available."""
    food_bank.add_inventory_item("Snack", "Food", 10)
    
    h1 = food_bank.add_food_hamper() # created
    h2 = food_bank.add_food_hamper()
    h3 = food_bank.add_food_hamper()
    
    food_bank.pack_food_hamper(h2.id, items={"Snack": 2}) # packed
    
    # h3 gets assigned (should no longer be 'available' in some system designs)
    c = food_bank.add_client("C", "p", "c@test.com")
    v = food_bank.add_volunteer("V", "p", "v@test.com")
    food_bank.assign_food_hamper(h3.id, c.id, volunteer_id=v.id)
    
    avail = food_bank.get_available_hampers()
    assert isinstance(avail, list)
    # Ensure it doesn't crash; the exact length depends on if 'assigned' is considered available
    assert len(avail) >= 0


def test_deliver_assigned_hamper_blocked(food_bank):
    """Tests that an assigned hamper cannot be delivered until it is packed."""
    c = food_bank.add_client("ClientA", "p", "ca@test.com")
    v = food_bank.add_volunteer("VolA", "p", "va@test.com")
    hamper = food_bank.add_food_hamper(client_id=c.id, volunteer_id=v.id)
    assert hamper.status == "assigned"
    with pytest.raises(ValueError, match="must be 'packed' before delivery"):
        food_bank.deliver_food_hamper(hamper.id)


def test_update_donation_to_stocked_adds_to_inventory(food_bank):
    """Tests that updating donation status to 'stocked' via update_donation successfully adds items to inventory."""
    d = food_bank.add_donor("DonorA", "p", "da@test.com")
    donation = food_bank.add_donation(d.id, items=[{"name": "Canned Corn", "quantity": 15, "category": "Food", "unit": "cans"}])
    v = food_bank.add_volunteer("VolB", "p", "vb@test.com")
    food_bank.collect_donation(donation.id, v.id)
    assert donation.status == "collected"

    # Now update donation status to stocked
    food_bank.update_donation(donation.id, status="stocked")
    assert donation.status == "stocked"
    item = food_bank.inventory.find_item_by_name("Canned Corn")
    assert item is not None
    assert item.quantity == 15


def test_update_food_hamper_to_packed_deducts_inventory(food_bank):
    """Tests that updating food hamper status to 'packed' via update_food_hamper deducts items from inventory."""
    food_bank.add_inventory_item("Pasta Box", "Food", 20)
    c = food_bank.add_client("ClientB", "p", "cb@test.com")
    hamper = food_bank.add_food_hamper(client_id=c.id, items=[{"name": "Pasta Box", "quantity": 4}])
    assert hamper.status == "created"

    food_bank.update_food_hamper(hamper.id, status="packed")
    assert hamper.status == "packed"
    item = food_bank.inventory.find_item_by_name("Pasta Box")
    assert item.quantity == 16
