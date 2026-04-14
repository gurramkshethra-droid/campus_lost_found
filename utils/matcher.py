from models import Item, Match
from extensions import db

THRESHOLD = 50


def score_keywords(description_a, description_b):
    if not description_a or not description_b:
        return 0

    words_a = set(word.lower() for word in description_a.split() if len(word) > 3)
    words_b = set(word.lower() for word in description_b.split() if len(word) > 3)
    matches = words_a.intersection(words_b)
    return min(30, len(matches) * 10)


def compute_match_score(source, target):
    score = 0
    if source.category == target.category:
        score += 30
    if source.location.lower() == target.location.lower():
        score += 25
    if source.color and target.color and source.color.lower() == target.color.lower():
        score += 10
    score += score_keywords(source.description, target.description)
    return score


def find_matches_for_item(item):
    if item.type not in ('lost', 'found'):
        return []

    opposite_type = 'found' if item.type == 'lost' else 'lost'
    candidates = Item.query.filter_by(type=opposite_type, status='active').all()
    created_matches = []

    for candidate in candidates:
        score = compute_match_score(item, candidate)
        if score >= THRESHOLD:
            lost_item = item if item.type == 'lost' else candidate
            found_item = candidate if item.type == 'lost' else item
            existing = Match.query.filter_by(
                lost_item_id=lost_item.id,
                found_item_id=found_item.id
            ).first()
            if not existing:
                match = Match(lost_item_id=lost_item.id,
                              found_item_id=found_item.id,
                              match_score=score)
                db.session.add(match)
                created_matches.append(match)

    if created_matches:
        db.session.commit()

    return created_matches
