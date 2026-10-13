from app.core.password import hash_password, verify_password


def test_password_hashing():
    password = "ExamplePassword123!"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed)


def test_invalid_password():
    hashed = hash_password("CorrectPassword123!")

    assert not verify_password("WrongPassword123!", hashed)


def test_invalid_hash():
    assert not verify_password("password", "invalid-hash")


def test_unique_hashes():
    password = "ExamplePassword123!"

    first = hash_password(password)
    second = hash_password(password)

    assert first != second