"""ANE NLP-extras (#97) — Token-Classification / Named-Entity Recognition via Apple NaturalLanguage NLTagger,
on the ANE, GPU-free. Extends ane_route.py (#93).

    from ane_nlp import ner, pos
    ner("Tim Cook visited Paris with Apple")   # [('Tim Cook','PersonalName'), ('Paris','PlaceName'), …]
    pos("the agent fixed the test")            # [('the','Determiner'), ('agent','Noun'), …]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))


def _tag(text, scheme_name, keep):
    """Tag each word on the ANE. Returns [(word, tag) …] for tags in `keep`. tagAtIndex surfaces ONLY the tag
    string in pyobjc (not the NSRange out-param), so we walk the words ourselves and tag at each start index."""
    import NaturalLanguage as NL
    from Foundation import NSString
    scheme = getattr(NL, scheme_name)
    tagger = NL.NLTagger.alloc().initWithTagSchemes_([scheme])
    tagger.setString_(NSString.stringWithString_(text))
    out = []
    idx = 0
    for word in text.split():
        start = text.index(word, idx)
        tag = tagger.tagAtIndex_unit_scheme_tokenRange_(start, NL.NLTokenUnitWord, scheme, None)
        if tag is not None and str(tag) in keep:
            out.append((word, str(tag)))
        idx = start + len(word)
    return out


def ner(text):
    """#97: Named-Entity Recognition on the ANE. Returns [(entity, type) …] (Personal/Place/Organization)."""
    return _tag(text, "NLTagSchemeNameType", {"PersonalName", "PlaceName", "OrganizationName"})


def pos(text):
    """#97: Token Classification / Part-of-Speech on the ANE. Returns [(token, class) …]."""
    return _tag(text, "NLTagSchemeLexicalClass",
                {"Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Determiner", "Preposition", "Number"})


if __name__ == "__main__":
    ents = ner("Tim Cook visited Paris to meet engineers at Apple and Google")
    tags = pos("the agent quickly fixed the failing test")
    print(f"  ner -> {ents}")
    print(f"  pos -> {tags[:6]}")
    ok = any(t == "PlaceName" for _, t in ents) and len(tags) >= 4
    print(f"  ane_nlp selftest {'PASS' if ok else 'CHECK'} — NER + POS on the Neural Engine")
