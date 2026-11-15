import argparse
import json
import os
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from .pipeline import build, read_jsonl, validate, write_jsonl
from .seeds import LANGUAGES, digest, make_seeds, render

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description="Build draft Track 1 materials; no evaluation model calls.")
    parser.add_argument("command", choices=("doctor", "seeds", "templates", "adaption", "validate", "build"))
    parser.add_argument("--seeds", type=Path, default=ROOT/"data/seeds/pilot.jsonl")
    parser.add_argument("--translations", type=Path, default=ROOT/"data/generated/translations.jsonl")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT/"configs/pilot.json")
    parser.add_argument("--require-reviewed", action="store_true")
    args = parser.parse_args()
    from dotenv import dotenv_values
    env_path = Path(os.environ.get("TRACK1_ENV_FILE", str(ROOT/".env")))
    if env_path.is_file():
        key = dotenv_values(env_path).get("ADAPTION_API_KEY")
        if key and not os.environ.get("ADAPTION_API_KEY"):
            os.environ["ADAPTION_API_KEY"] = key
    config = json.loads(args.config.read_text())
    if tuple(config["languages"]) != LANGUAGES or config["peer_count"] != 3:
        parser.error("This pilot requires en/zh/vi and three scripted peers")
    try:
        if args.command == "doctor":
            try:
                sdk = version("adaption")
            except PackageNotFoundError:
                sdk = None
            print(json.dumps({"sdk_version": sdk, "sdk_matches_pin": sdk == config["sdk_version"],
                              "api_key_configured": bool(os.environ.get("ADAPTION_API_KEY")),
                              "network_calls": 0, "generator_model": config["generation_model"]}, indent=2))
            return
        if args.command == "seeds":
            seeds = make_seeds()
            if len(seeds) != config["seed_count"]:
                raise ValueError("Configured seed count does not match pilot")
            write_jsonl(args.output or args.seeds, seeds)
            print(f"Wrote {len(seeds)} deterministic seed cases")
            return
        seeds = read_jsonl(args.seeds)
        if args.command in ("templates", "adaption"):
            if args.command == "adaption":
                from .adaption_client import translate
                if version("adaption") != config["sdk_version"]:
                    raise ValueError("Installed SDK differs from configured version")
            rows = []
            for seed in seeds:
                for language in LANGUAGES:
                    if args.command == "adaption" and language != "en":
                        row = translate(seed, language, config["generation_model"], ROOT/"data/generated/cache")
                    else:
                        row = render(seed, language)
                    rows.append(row)
                    if args.command == "adaption":
                        print(f"Prepared {seed['case_id']} {language}", flush=True)
            report = validate(seeds, rows)
            if report["errors"]:
                raise ValueError("; ".join(report["errors"][:5]))
            write_jsonl(args.output or args.translations, rows)
            print(f"Wrote {len(rows)} draft language records; all require human review")
            return
        rows = read_jsonl(args.translations)
        if args.command == "validate":
            report = validate(seeds, rows, args.require_reviewed)
            text = json.dumps(report, ensure_ascii=False, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text+"\n")
            print(text)
            if report["errors"]:
                raise SystemExit(1)
        else:
            review = config.get("shared_prompt_review", {})
            if args.require_reviewed and (review.get("status") != "approved" or not review.get("reviewer")):
                raise ValueError("Shared instruction/peer templates require review in config")
            variants = list(build(seeds, rows, args.require_reviewed, config["peer_count"]))
            output = args.output or ROOT/"data/generated/pilot-variants.jsonl"
            write_jsonl(output, variants)
            manifest = {"dataset_hash": digest(variants),
                        "seed_count": len(seeds), "variant_count": len(variants), "config": config,
                        "review_required": args.require_reviewed, "evaluation_calls": 0,
                        "note": "Variants are prompts, not independent samples or model results; initial UNKNOWN is legitimate for fictional facts."}
            output.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
            print(json.dumps(manifest, indent=2))
    except (ValueError, OSError, KeyError, PackageNotFoundError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    except Exception as exc:
        # Provider exception messages can contain request data; do not dump them.
        parser.exit(2, f"Provider or unexpected failure ({type(exc).__name__}); no success claimed.\n")


if __name__ == "__main__":
    main()
