"""The #44 and #50 experiments: the nearest deck on a saved combined embedding, or on the bag of cards (--bag), compared with a baseline run.

It's fitted on scheme 1's TRAIN decks ("default": train {VERIFIED}) with no validation decks, since nothing is tuned, so no row is flagged as tuned on.
--scheme picks another scheme on snapshot 1, such as #59's "default, labels at season 39".
It's saved, run on {HELD_OUT, VALIDATION} and reported into docs/experiments/. The test seasons aren't used. It composes existing functions only.
The report is rendered by evaluation.report in place of this process, so the fitted model's memory is freed first (a report holds every
candidate of two runs, about 4.4 GB for 20,173 decks).

    uv run --group archetypes python -m archetype_classifier.experiments.embedding_nearest_deck \\
        --embedding potion__masked__average__w0.5-0.1667-0.1667-0.1667__fit1-38__emb1-39 --label text_and_numbers \\
        --baseline-run 4 --min-decks 10 --date 20261008 --pr 48

#50 adds card weights and copies to the nearest deck, and the bag of cards:

    ... --embedding <name> --weights idf --copies sqrt --label idf_sqrt --baseline-run 8 ...
    ... --bag --copies sqrt --label idf_sqrt --baseline-run 8 ...
    ... --embedding <name> --weights idf --copies sqrt --unseen-weight typical --label idf_sqrt_typical --baseline-run 11 ...
"""
import argparse
import os
import sys
import time
from pathlib import Path

from archetype_classifier.data_loading import loader
from archetype_classifier.data_loading.slices import build_deck_set, deck_ids_hash
from archetype_classifier.data_loading.splits import Split
from archetype_classifier.evaluation.metrics import ArchetypeTree
from archetype_classifier.evaluation.model import JSON, FitContext, Model, build_predict_decks, build_training_decks
from archetype_classifier.evaluation.store import ModelRecord, save_model, save_run
from archetype_classifier.models.bag_nearest import BagNearestDeck
from archetype_classifier.models.embedding_nearest import EmbeddingNearestDeck

SCHEME = 'default'
TRAIN, VALIDATION, SCOPE = frozenset({Split.TRAIN}), frozenset[Split](), frozenset({Split.HELD_OUT, Split.VALIDATION})
OUT = Path(__file__).parents[1] / 'docs' / 'experiments'


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--embedding', help='the saved combined embedding, by its file name without .npz (not with --bag)')
    parser.add_argument('--bag', action='store_true', help='the bag of cards instead of an embedding (#50)')
    parser.add_argument('--weights', choices=['none', 'idf'], help="the nearest deck's card weights (#50); left out, version 2's model")
    parser.add_argument('--unseen-weight', choices=['idf', 'typical'], help="with --weights idf, how unseen cards weigh (#50); left out, idf")
    parser.add_argument('--copies', choices=['linear', 'sqrt'], help='how copies count (#50); left out, linear for the embedding and sqrt for the bag')
    parser.add_argument('--label', required=True, help='a short name for the report file, e.g. text_and_numbers')
    parser.add_argument('--baseline-run', type=int, required=True, help='the run to compare with, deck by deck')
    parser.add_argument('--min-decks', type=int, required=True, help='the fewest decks an archetype needs to count in macro averages')
    parser.add_argument('--pr', type=int, action='append', default=[], help='a PR that produced the run (repeatable)')
    parser.add_argument('--date', required=True, help='YYYYMMDD, for the report file name')
    parser.add_argument('--scheme', default=SCHEME, help=f"the split scheme, by name (default: '{SCHEME}')")
    args = parser.parse_args()
    if args.bag == bool(args.embedding) or (args.bag and (args.weights or args.unseen_weight)):
        parser.error('give --embedding (with optional --weights and --unseen-weight) or --bag, not both')

    edb = loader.experiments_db()
    scheme_id = int(edb.value('SELECT id FROM split_scheme WHERE name = %s', [args.scheme]))
    snapshot = loader.load_snapshot(edb, 1, scheme_id)
    train, scored = build_deck_set(snapshot, TRAIN), build_deck_set(snapshot, SCOPE)
    training = build_training_decks(train, loader.load_contents(train.decks))
    predict_decks = build_predict_decks(scored, loader.load_contents(scored.decks))
    context = FitContext(ArchetypeTree(snapshot.archetypes), loader.load_legal_cards({d.season_id for d in train.decks.values()}), seed=0)
    print(f'{len(training)} training decks, {len(predict_decks)} decks to predict')

    options: dict[str, JSON] = {k: v for k, v in (('weights', args.weights), ('copies', args.copies), ('unseen_weight', args.unseen_weight)) if v is not None}
    model: Model = BagNearestDeck(options) if args.bag else EmbeddingNearestDeck({'embedding': args.embedding, **options})
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
    print(f'{state["training_rows"]} training rows, {state.get("skipped_copies", 0)} skipped copies; fitted in {fit_seconds:.0f}s, model {model_id}, run {run_id}')

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'{args.date}_{"bag" if args.bag else "embedding"}_nearest_{args.label}.md'
    report = [sys.executable, '-m', 'archetype_classifier.evaluation.report', str(run_id), '--baseline', str(args.baseline_run),
              '--min-decks', str(args.min_decks), *(f'--pr={pr}' for pr in args.pr), '--out', str(path)]
    sys.stdout.flush()
    os.execv(sys.executable, report)

if __name__ == '__main__':
    main()
