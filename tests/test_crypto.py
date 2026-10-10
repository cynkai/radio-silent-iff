from iff import crypto, config


def test_hkdf_rfc5869_case1():
    # RFC 5869 Appendix A, Test Case 1
    ikm = bytes.fromhex("0b" * 22)
    salt = bytes.fromhex("000102030405060708090a0b0c")
    info = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
    okm = crypto.hkdf(ikm, salt, info, 42)
    assert okm.hex() == (
        "3cb25f25faacd57a90434f64d0362f2a"
        "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
        "34007208d5b887185865"
    )


def test_tag_deterministic_and_nonce_sensitive():
    mk = b"\x01" * 32
    uid = bytes.fromhex("0000000a")
    uk = crypto.unit_key(mk, 100, uid)
    n1 = b"\xaa" * config.NONCE_BYTES
    n2 = b"\xab" * config.NONCE_BYTES
    t1 = crypto.response_tag(uk, n1, uid, 100)
    t1b = crypto.response_tag(uk, n1, uid, 100)
    t2 = crypto.response_tag(uk, n2, uid, 100)
    assert t1 == t1b          # deterministic
    assert t1 != t2           # one-byte nonce change flips the tag
    assert len(t1) == config.TAG_BYTES


def test_epoch_change_changes_unit_key():
    mk = b"\x02" * 32
    uid = bytes.fromhex("0000000a")
    assert crypto.unit_key(mk, 100, uid) != crypto.unit_key(mk, 101, uid)
