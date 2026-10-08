"""The #44 experiment: the nearest deck on a saved combined embedding, compared with a baseline run.

It's fitted on scheme 1's TRAIN decks ("default": train {VERIFIED}) with no validation decks, since nothing is tuned, so no row is flagged as tuned on.
It's saved, run on {HELD_OUT, VALIDATION} and reported into docs/experiments/. The test seasons aren't used. It composes existing functions only.

    uv run --group archetypes python -m archetype_classifier.experiments.embedding_nearest_deck \\
        --embedding potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39 --label text_and_numbers \\
        --baseline-run 4 --min-decks 10 --date 20261008 --pr 48
"""
import argparse
import time
from pathlib import Path

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import build_deck_set, deck_ids_hash
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import FitContext, build_predict_decks, build_training_decks
from archetype_classifier.evaluation.report import render_report
from archetype_classifier.evaluation.store import ModelRecord, save_model, save_run
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck

SCHEME = 'default'
TRAIN, VALIDATION, SCOPE = frozenset({Split.TRAIN}), frozenset[Split](), frozenset({Split.HELD_OUT, Split.VALIDATION})
OUT = Path(__file__).parents[1] / 'docs' / 'experiments'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--embedding', required=True, help='the saved combined embedding, by its file name without .npz')
    parser.add_argument('--label', required=True, help='a short name for the report file, e.g. text_and_numbers')
    parser.add_argument('--baseline-run', type=int, required=True, help='the run to compare with, deck by deck')
    parser.add_argument('--min-decks', type=int, required=True, help='the fewest decks an archetype needs to count in macro averages')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the run (repeatable)')
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the report file name')
    args = parser.parse_args()

    edb = loader.experiments_db()
    scheme_id = int(edb.value('SELECT id FROM split_scheme WHERE name = %s', [SCHEME]))
    snapshot = loader.load_snapshot(edb, 1, scheme_id)
    train, scored = build_deck_set(snapshot, TRAIN), build_deck_set(snapshot, SCOPE)
    training = build_training_decks(train, loader.load_contents(train.decks))
    predict_decks = build_predict_decks(scored, loader.load_contents(scored.decks))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in train.decks.values()}), seed=0)
    print(f'{len(training)} training decks, {len(predict_decks)} decks to predict')

    model = EmbeddingNearestDeck({'embedding': args.embedding})
    start = time.perf_counter()
    model.fit(training, [], context)
    fit_seconds = time.perf_counter() - start
    record = ModelRecord(model.name, model.version, model.params, 1, scheme_id, context.seed, TRAIN, VALIDATION, len(training),
                         deck_ids_hash(d.deck.deck_id for d in training), 0, deck_ids_hash([]), fit_seconds)
    model_id = save_model(edb, model, record)
    start = time.perf_counter()
    predictions = model.predict(predict_decks)
    run_id = save_run(edb, model_id, SCOPE, predictions, seconds=time.perf_counter() - start)
    state = model.state()
    print(f'{state["training_rows"]} training rows, {state["skipped_copies"]} skipped copies; fitted in {fit_seconds:.0f}s, model {model_id}, run {run_id}')

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{args.date}_embedding_nearest_{args.label}.md'
    path.write_text(render_report(edb, run_id, args.min_decks, baseline_run_id=args.baseline_run, prs=args.pr))
    print(f'Wrote {path}')

if __name__ == '__main__':
    main()
