"""The #6 experiment: today's guesser, as the similarity baseline, at the site's fixed threshold of 20 and at a threshold tuned on season 39.

Both are fitted on scheme 2's TRAIN decks ("similarity baseline": train {VERIFIED, UNVERIFIED}), saved, run on {HELD_OUT, VALIDATION}, and reported
into docs/experiments/. The test seasons aren't used. It composes existing functions only.

    uv run python -m archetype_classifier.experiments.similarity_baseline --min-decks 20 --pr 34
    uv run python -m archetype_classifier.experiments.similarity_baseline --threshold 20 --min-decks 10 --date 20261012  # The site's threshold only.
"""
import argparse
import time
from pathlib import Path

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import build_deck_set, deck_ids_hash
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, build_labelled_decks, build_predict_decks, build_training_decks
from archetype_classifier.evaluation.report import render_report
from archetype_classifier.evaluation.store import ModelRecord, save_model, save_run
from archetype_classifier.models.similarity import SimilarityBaseline

SCHEME = 'similarity baseline'
TRAIN, VALIDATION, SCOPE = frozenset({Split.TRAIN}), frozenset({Split.VALIDATION}), frozenset({Split.HELD_OUT, Split.VALIDATION})
OUT = Path(__file__).parents[1] / 'docs' / 'experiments'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--min-decks', type=int, required=True, help='the fewest decks an archetype needs to count in macro averages')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the runs (repeatable)')
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the report file names')
    parser.add_argument('--threshold', action='append', type=threshold_arg, help="a whole-number threshold or 'tuned' (repeatable; default: 20 and tuned)")
    args = parser.parse_args()

    edb = loader.experiments_db()
    scheme_id = int(edb.value('SELECT id FROM split_scheme WHERE name = %s', [SCHEME]))
    snapshot = loader.load_snapshot(edb, 1, scheme_id)
    train, validation, scored = (build_deck_set(snapshot, splits) for splits in (TRAIN, VALIDATION, SCOPE))
    training = build_training_decks(train, loader.load_contents(train.decks))
    labelled = build_labelled_decks(validation, loader.load_contents(validation.decks))
    predict_decks = build_predict_decks(scored, loader.load_contents(scored.decks))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in train.decks.values()}), seed=0)
    print(f'{len(training)} training decks, {len(labelled)} validation decks, {len(predict_decks)} decks to predict')

    run_ids = {}
    for threshold in args.threshold or [20, 'tuned']:
        label = 'tuned' if threshold == 'tuned' else f'fixed{threshold}'
        model = SimilarityBaseline({'threshold': threshold})
        start = time.perf_counter()
        model.fit(training, labelled, context)
        fit_seconds = time.perf_counter() - start
        record = ModelRecord(model.name, model.version, model.params, 1, scheme_id, context.seed, TRAIN, VALIDATION, len(training),
                             deck_ids_hash(d.deck.deck_id for d in training), len(labelled), deck_ids_hash(d.deck.deck_id for d in labelled), fit_seconds)
        model_id = save_model(edb, model, record)
        start = time.perf_counter()
        predictions = model.predict(predict_decks)
        run_ids[label] = save_run(edb, model_id, SCOPE, predictions, seconds=time.perf_counter() - start)
        print(f'{label}: threshold {model.threshold}, fitted in {fit_seconds:.0f}s, model {model_id}, run {run_ids[label]}')

    OUT.mkdir(parents=True, exist_ok=True)
    for label, run_id in run_ids.items():
        baseline = run_ids.get('fixed20') if label == 'tuned' else None  # The tuned threshold is compared with the site's.
        path = OUT / f'{args.date}_similarity_{label}.md'
        path.write_text(render_report(edb, run_id, args.min_decks, baseline_run_id=baseline, prs=args.pr))
        print(f'Wrote {path}')

def threshold_arg(text: str) -> int | str:
    return text if text == 'tuned' else int(text)

if __name__ == '__main__':
    main()
