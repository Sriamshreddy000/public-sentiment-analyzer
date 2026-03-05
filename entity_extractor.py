import spacy

nlp = spacy.load("en_core_web_sm")

def extract_entities(text):
    doc = nlp(text)

    entities = []
    for ent in doc.ents:
        if ent.label_ in ["GPE", "ORG", "PERSON"]:
            entities.append(ent.text)

    # remove duplicates
    entities = list(dict.fromkeys(entities))

    return entities[:3]  # keep top 3