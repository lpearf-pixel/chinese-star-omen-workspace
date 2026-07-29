# B9 Vertical Slice Runbook

This runbook separates hermetic hosted-CI verification from the required local/self-hosted macOS renderer evidence. It never writes official Qdrant, never accesses `local_kb_default`, and never publishes content.

## 1. Preconditions

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Release line: stable/kaiyuan-v2
Python: 3.12+
Stellarium: supported 26.x series
FFmpeg: version recorded by the local evidence record
Output package: generated local directory only
```

Before using the runbook:

1. verify the current remote `stable/kaiyuan-v2` HEAD;
2. verify all open PRs;
3. use a clean checkout or detached worktree;
4. do not configure any official ingest or production collection;
5. keep all generated output under the ignored local directories described below.

## 2. Hermetic hosted-CI gate

From the repository root:

```bash
python3.12 -m venv .venv-b9
source .venv-b9/bin/activate
python -m pip install -e apps/star-omen

cd apps/star-omen
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  python -m pytest -q tests/video_pipeline/package_review
```

This gate verifies SRT, manifest, no-overwrite publication, review hashes, bounded preview argv, local-capability schema and both hermetic vertical paths. It does not launch Stellarium or FFmpeg.

## 3. Build the fixed July 21 smoke package

The following command deliberately uses the repository's fixed test fixture and synthetic review fixture. It is suitable only for renderer smoke testing and does not constitute publication approval.

From `apps/star-omen`:

```bash
mkdir -p data/generated_video_packages
rm -rf data/generated_video_packages/july-21-local-smoke

PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
from pathlib import Path

from src.video_pipeline.vertical_package import publish_vertical_package
from tests.video_pipeline.package_review.test_vertical_package_e2e_v1 import july_build

_event, _result, _editorial, _script, build = july_build()
output = Path("data/generated_video_packages/july-21-local-smoke")
publish_vertical_package(output_dir=output, build=build)
print(output.resolve())
print(build.manifest.model_dump_json(indent=2))
PY
```

The package must contain:

```text
manifest.json
astronomy-event.json
rule-assessment.json
evidence-bundle.json
video-package.json
editorial-package.json
scene.ssc
subtitles.srt
preview-command.json
review-bundle.json
review-gate.json
```

It must not contain `preview.mp4` until a real local preview command is executed.

## 4. Inspect the structured package

From the package directory:

```bash
python - <<'PY'
import hashlib
import json
from pathlib import Path

root = Path(".")
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
for entry in manifest["members"]:
    path = root / entry["path"]
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert len(raw) == entry["byte_size"], entry["path"]
    assert digest == entry["sha256"], entry["path"]
print("manifest verification: PASS")
PY
```

Do not edit any member after this verification. Any edit requires a fresh package build and fresh review hashes.

## 5. Run the bounded FFmpeg preview locally

The generated `preview-command.json` contains an argv array and timeout. Execute it without a shell:

```bash
cd data/generated_video_packages/july-21-local-smoke

python - <<'PY'
import json
import subprocess
from pathlib import Path

payload = json.loads(Path("preview-command.json").read_text(encoding="utf-8"))
assert payload["shell"] is False
assert payload["output_path"] == "preview.mp4"
subprocess.run(
    payload["argv"],
    check=True,
    timeout=payload["timeout_seconds"],
    shell=False,
)
print(Path("preview.mp4").resolve())
PY
```

The local operator must confirm:

- output resolution is 1080x1920;
- duration is approximately 80 seconds;
- subtitles are readable and ordered;
- there is no audio requirement;
- this is `preview.mp4`, never `final.mp4`.

The MP4 hash is meaningful only together with the exact FFmpeg version and platform. Cross-platform byte equality is not required.

## 6. Run and inspect the Stellarium script

`scene.ssc` is a deterministic renderer script. It is not a scientific evidence source. Load it in the installed Stellarium 26.x environment using the local application's supported script-loading workflow.

The local operator must verify:

- the script uses the UTC time shown in `astronomy-event.json`;
- longitude, latitude and elevation match the event observer;
- the Moon and mapped target can be selected;
- tracking, time rate and GUI state are restored at the end;
- no screenshot, file, URL, include, eval or shell command is present.

Capture at most 30 screenshots under:

```text
apps/star-omen/data/local_renderer_evidence/screenshots/
```

Do not put screenshots inside the structured package. Record their relative paths, byte sizes and SHA-256 values in local capability evidence.

## 7. Create local capability evidence

First prepare screenshot hashes:

```bash
cd apps/star-omen
mkdir -p data/local_renderer_evidence

find data/local_renderer_evidence/screenshots -type f -name '*.png' -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 \
  > data/local_renderer_evidence/screenshot-sha256.txt
```

Then construct `LocalCapabilityEvidence/v1` with the public API. The operator must replace the example screenshot metadata with actual values and record the exact installed versions.

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from src.video_pipeline.capability import (
    ScreenshotEvidenceV1,
    build_local_capability_evidence,
    canonical_capability_evidence_bytes,
)
from src.video_pipeline.preview import PreviewCapabilityV1, PreviewCommandV1
from src.video_pipeline.stellarium import StellariumScriptV1

package = Path("data/generated_video_packages/july-21-local-smoke")
preview_command = PreviewCommandV1.model_validate_json(
    (package / "preview-command.json").read_text(encoding="utf-8")
)
script_content = (package / "scene.ssc").read_text(encoding="utf-8")
script = StellariumScriptV1(
    script_id=f"stellarium-script:{hashlib.sha256(script_content.encode('utf-8')).hexdigest()[:32]}",
    event_id=json.loads((package / "astronomy-event.json").read_text())["event_id"],
    editorial_package_id=json.loads((package / "editorial-package.json").read_text())["editorial_package_id"],
    stellarium_version="26.2.0",  # replace with the actual 26.x version
    commands=[
        "core.clear",
        "core.setGuiVisible",
        "core.setTimeRate",
        "core.setDate",
        "core.setObserverLocation",
        "core.selectObjectByName",
        "StelMovementMgr.setFlagTracking",
        "StelMovementMgr.zoomTo",
        "core.wait",
    ],
    total_wait_ms=80000,
    content=script_content,
    sha256=hashlib.sha256(script_content.encode("utf-8")).hexdigest(),
)
capability = PreviewCapabilityV1(
    ffmpeg_version="7.1.1",  # replace with the actual version
    enabled_features=["lavfi-color", "subtitles", "libx264"],
    max_timeout_seconds=120,
)

# Replace with actual screenshot records. Every path must remain repository-relative.
screenshots = []
for path in sorted(Path("data/local_renderer_evidence/screenshots").glob("*.png")):
    raw = path.read_bytes()
    screenshots.append(
        ScreenshotEvidenceV1(
            path=path.relative_to(Path("data/local_renderer_evidence")).as_posix(),
            byte_size=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
        )
    )

record = build_local_capability_evidence(
    evidence_id="local-capability:macos-renderer-v1",
    captured_at=datetime.now(timezone.utc),
    platform="macOS",
    architecture=platform.machine(),
    stellarium_script=script,
    preview_command=preview_command,
    preview_capability=capability,
    preview_observed=(package / "preview.mp4").is_file(),
    visual_review_status="approved",
    screenshots=screenshots,
)
out = Path("data/local_renderer_evidence/local-capability-evidence.json")
out.write_bytes(canonical_capability_evidence_bytes(record))
print(out.resolve())
PY
```

The command intentionally fails if visual approval is claimed without an observed preview and screenshot evidence.

## 8. Evidence handoff

Create a local archive containing only:

```text
local-capability-evidence.json
screenshot-sha256.txt
screenshots/*.png
```

Do not include `.env`, keys, full corpus, Qdrant data, machine logs containing secrets, or private absolute paths.

Example:

```bash
cd apps/star-omen/data/local_renderer_evidence
tar -czf ../b9-local-g6-evidence.tar.gz \
  local-capability-evidence.json \
  screenshot-sha256.txt \
  screenshots
```

The evidence archive is reviewed before any B9 completion claim. A local preview alone does not authorize publishing and does not convert blocked classical evidence into a quotation.

## 9. Failure handling

- Existing output directory: stop; never overwrite it. Move it manually only after preserving its evidence.
- Manifest hash mismatch: discard the entire generated package and rebuild.
- Stellarium capability/version mismatch: mark G6 blocked; do not silently substitute a different script.
- FFmpeg timeout or failure: keep logs outside the structured package and mark preview unobserved.
- Missing screenshot or visual rejection: `visual_review_status` cannot be approved.
- Any corpus, Qdrant or ingest activity: stop immediately; it is outside this runbook.
