
from pathlib import Path
import json

from name_shortener_service import (
    NameShortenerService,
    load_examples_from_csv,
    custom_lines_are_logical,
    normalize_space,
)

ARTIFACT_DIR = Path("artifacts")
TRAIN_CSV = Path("train.csv")
VALID_CSV = Path("valid.csv")
META_FILE = ARTIFACT_DIR / "dataset_meta.json"


def current_dataset_meta():
    train_examples = load_examples_from_csv(str(TRAIN_CSV))
    valid_examples = load_examples_from_csv(str(VALID_CSV))
    return {
        "train_rows": len(train_examples),
        "valid_rows": len(valid_examples),
    }, train_examples, valid_examples


def artifacts_match_current_data(meta: dict) -> bool:
    if not META_FILE.exists():
        return False
    try:
        saved = json.loads(META_FILE.read_text(encoding="utf-8"))
    except Exception:
        return False
    return saved == meta


def ensure_service():
    meta, train_examples, valid_examples = current_dataset_meta()

    if ARTIFACT_DIR.exists() and (ARTIFACT_DIR / "model.pt").exists() and artifacts_match_current_data(meta):
        print("Loading existing artifacts...")
        service = NameShortenerService.load(str(ARTIFACT_DIR))
        return service, train_examples, valid_examples

    print("Training a new model...")
    service = NameShortenerService.from_examples(train_examples)
    service.fit(train_examples, valid_examples=valid_examples, epochs=35, batch_size=16, lr=1e-3)
    service.save(str(ARTIFACT_DIR))
    ARTIFACT_DIR.mkdir(exist_ok=True)
    META_FILE.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return service, train_examples, valid_examples


def print_top3(preds):
    print("\nTop suggestions:")
    for i, p in enumerate(preds, start=1):
        tag = " [exact memory]" if p["actions"] == ["EXACT_MEMORY"] else ""
        print(f"{i}. {p['line1']} | {p['line2']} | score={p['score']}{tag}")


def do_online_update(service, full_name, line1, line2):
    service.online_update_from_labeled_lines(
        full_name=full_name,
        name_line1=line1,
        name_line2=line2,
        replay_examples=None,
        steps=0,
        update_model=False,
    )
    service.save(str(ARTIFACT_DIR))
    print("Updated specific memory for this name only.")
    print(f"Pending updates for future retraining: {service.pending_retrain_count()}")
    if service.should_retrain():
        print("Retraining threshold reached. You can retrain later and then clear the pending buffer.")


def main():
    service, train_examples, valid_examples = ensure_service()

    while True:
        full_name = input("\nFull name (or 'quit'): ").strip()
        if full_name.lower() in {"quit", "exit"}:
            break

        preds = service.predict_top3(full_name, max_chars_per_line=22)
        if not preds:
            print("No valid 2-line suggestions found.")
            continue

        print_top3(preds)
        print("4. Enter a custom 2-line choice")
        print("5. Retrain now from train+valid+pending updates, then clear pending memory")
        choice = input("Pick 1, 2, 3, 4, 5, or press Enter to skip: ").strip()

        if choice in {"1", "2", "3"}:
            idx = int(choice) - 1
            if idx < len(preds):
                picked = preds[idx]
                do_online_update(service, full_name, picked["line1"], picked["line2"])
            else:
                print("That option was not available.")
        elif choice == "4":
            custom_line1 = normalize_space(input("Custom line 1: "))
            custom_line2 = normalize_space(input("Custom line 2: "))
            ok, _, message = custom_lines_are_logical(full_name, custom_line1, custom_line2, max_chars_per_line=22)
            if not ok:
                print(f"Custom choice rejected: {message}")
                continue
            do_online_update(service, full_name, custom_line1, custom_line2)
        elif choice == "5":
            pending_examples = service.pending_retrain_buffer.to_examples()
            if not pending_examples:
                print("No pending updates to retrain on.")
                continue

            combined_train = train_examples + pending_examples
            print(f"Retraining with {len(train_examples)} original train + {len(pending_examples)} pending updates...")
            service = NameShortenerService.from_examples(combined_train)
            service.fit(combined_train, valid_examples=valid_examples, epochs=25, batch_size=16, lr=1e-3)
            service.flush_pending_after_retrain()
            service.save(str(ARTIFACT_DIR))
            print("Retraining complete. Pending buffer and exact-name memory cleared.")
        else:
            print("Skipped online update.")


if __name__ == "__main__":
    main()
