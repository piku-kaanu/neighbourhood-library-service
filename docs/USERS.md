# Creating Admin and Member Users

## Prerequisites

- Database tables created: `python -m app.core.create_tables`
- At least one **library member** exists (for member users): add via **Members → Add member** in the app

---

## Super Admin (full access)

Creates the first admin user if no users exist.

```bash
python -m app.core.seed_admin
```

- **Username:** `admin`
- **Password:** `admin`
- **Role:** SUPER_ADMIN (all permissions)

**Important:** Change the password after first login. (You can do this by updating the database or adding a “change password” feature.)

To create another admin, add a user manually in the database with `role='SUPER_ADMIN'` and `member_id=NULL`, and set `password_hash` using the same hashing as in the app (e.g. run `from app.core.auth import hash_password; print(hash_password("yourpassword"))` in a shell).

---

## Member User (books list + my borrows)

When you **add a member** via **Members → Add member**, a login user is created automatically for that member. After saving, the members list shows a one-time message with a **temporary password**. The member can log in with their **email** as username and that temporary password (they should change it later if you add a “change password” feature).

If you need to create a member user for an existing member (e.g. one added before this feature), or to set a specific password, use the script:

```bash
python -m app.core.seed_member_user <member_email> <password> [username]
```

- **member_email:** Email of an existing member (must already exist in **Members**).
- **password:** Login password for this user.
- **username:** Optional. If omitted, the member’s email is used as the username.

**Examples:**

```bash
# User logs in with email as username and password "hello"
python -m app.core.seed_member_user john@example.com hello

# Custom username
python -m app.core.seed_member_user john@example.com hello john
```

Then the user can log in with that username and password and will see only their own borrows under **My borrows**.

---

## Summary

| Role         | How to create                          | Permissions                          |
|-------------|----------------------------------------|--------------------------------------|
| SUPER_ADMIN | `python -m app.core.seed_admin`        | All: books, members, borrow, list    |
| MEMBER      | **Automatic** when adding a member (temp password shown once), or `python -m app.core.seed_member_user <email> <password> [username]` | Books (list), My borrows (own only) |
