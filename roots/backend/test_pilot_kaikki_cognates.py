#!/usr/bin/env python3
"""Small offline regression tests for the Kaikki cognate pilot parser."""

from pilot_kaikki_cognates import arabic_key, explicit_relations


def main():
    assert arabic_key("رَسُول") == "رسول"
    assert arabic_key("ءَايَة", loose=True) == arabic_key("آية", loose=True)
    entry = {
        "etymology_templates": [
            {"name": "cog", "args": {"1": "he", "2": "דִּין", "tr": "din", "t": "judgement"}},
            {"name": "inh", "args": {"1": "ar", "2": "sem-pro", "3": "*dīn-"}},
            {"name": "bor", "args": {"1": "ar", "2": "syc", "3": "ܕܝܢܐ"}},
            {"name": "cog", "args": {"1": "en", "2": "dean"}},
        ]
    }
    got = explicit_relations(entry)
    assert [(row["relation"], row["language_code"]) for row in got] == [
        ("cognate", "he"), ("inherited", "sem-pro")
    ]
    print("ok — Arabic normalization and explicit-relation filtering")


if __name__ == "__main__":
    main()
