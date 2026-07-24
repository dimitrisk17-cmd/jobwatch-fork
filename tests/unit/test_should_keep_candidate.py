"""Behavioral tests for the shared candidate-filter used by all discovery providers."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from discover.helpers import should_keep_candidate  # noqa: E402


def test_product_manager_title_passes_with_matching_term():
    assert should_keep_candidate(
        title="Senior Product Manager, Music",
        matched_terms=["product manager"],
        searchable_text="Senior Product Manager, Music. Lead our music discovery product.",
    )


def test_lead_product_title_passes_with_matching_term():
    assert should_keep_candidate(
        title="Lead Product Manager, Platform",
        matched_terms=["product manager"],
        searchable_text="Lead Product Manager, Platform.",
    )


def test_engineering_manager_passes_when_specialized_term_in_body():
    assert should_keep_candidate(
        title="Engineering Manager, Cryptography",
        matched_terms=["cryptography"],
        searchable_text="Engineering Manager, Cryptography. We build privacy-preserving systems.",
    )


def test_cryptography_engineer_still_passes():
    assert should_keep_candidate(
        title="Senior Cryptography Engineer",
        matched_terms=["cryptography"],
        searchable_text="Senior Cryptography Engineer. Build cryptographic primitives.",
    )


def test_account_executive_still_drops():
    assert not should_keep_candidate(
        title="Account Executive, EMEA",
        matched_terms=["product"],
        searchable_text="Account Executive, EMEA. Sell our product.",
    )


def test_marketing_manager_still_drops():
    assert not should_keep_candidate(
        title="Senior Marketing Manager",
        matched_terms=["product"],
        searchable_text="Senior Marketing Manager. Lead product marketing.",
    )


def test_sales_engineer_still_drops_via_function_token():
    assert not should_keep_candidate(
        title="Senior Sales Engineer",
        matched_terms=["product"],
        searchable_text="Senior Sales Engineer. Demo our product.",
    )


def test_engineering_manager_without_matched_term_still_drops():
    assert not should_keep_candidate(
        title="Engineering Manager",
        matched_terms=[],
        searchable_text="Engineering Manager. Generic listing body.",
    )


def test_product_designer_drops_in_crypto_term_set():
    # Even though "product" is now a technical-title hint, the term filter
    # still drops Product Designer when the track is searching for crypto terms.
    assert not should_keep_candidate(
        title="Product Designer",
        matched_terms=[],
        searchable_text="Product Designer at Plain.",
    )


def test_product_manager_with_operations_fragment_passes():
    # "operations" is a function exclude, but a full role-term match in the
    # title outranks it (real posting: Musixmatch on Lever).
    assert should_keep_candidate(
        title="Product Manager, AI & Content Operations",
        matched_terms=["product manager"],
        searchable_text="Product Manager, AI & Content Operations. Own AI-assisted lyrics workflows.",
    )


def test_operations_manager_without_role_term_still_drops():
    assert not should_keep_candidate(
        title="Sales Operations Manager",
        matched_terms=["product"],
        searchable_text="Sales Operations Manager. Support the product org.",
    )


def test_single_word_term_does_not_bypass_function_excludes():
    # "product" matching inside "Product Marketing Manager" must not defeat
    # the "marketing" exclude; only multi-word role terms bypass it.
    assert not should_keep_candidate(
        title="Product Marketing Manager",
        matched_terms=["product"],
        searchable_text="Product Marketing Manager. Position our product.",
    )


def test_head_of_product_passes_with_product_term():
    assert should_keep_candidate(
        title="Head of Product, Audio",
        matched_terms=["head of product"],
        searchable_text="Head of Product, Audio. Own the audio product line.",
    )
