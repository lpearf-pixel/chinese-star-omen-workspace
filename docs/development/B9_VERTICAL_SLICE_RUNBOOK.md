# B9 Vertical Slice Runbook

This runbook separates hermetic hosted-CI verification from required local/self-hosted macOS renderer evidence. It does not write official Qdrant, access `local_kb_default`, or publish content.

## 1. Preconditions

```text
Repository: lpearf-pixel/chinese-star-omen-workspace
Release line: stable/kaiyuan-v2
Python: 3.12+
Stellarium: supported 26.x series
FFmpeg and ffprobe: same installed toolchain
Output: ignored local directories only
```

Before running G6:

1. verify the current remote `stable/kaiyuan-v2` HEAD and all open PRs;
2. use a clean checkout or detached worktree;
3. install no production ingest or collection configuration;
4. preserve every prior output directory; do not delete it to reuse a name;
5. create a fresh timestamped package and evidence directory.

## 2. Hermetic test gate

From the repository root:

```bash
python3.12 -m venv .venv-b9
source .venv-b9/bin/activate
python -m pip install -e apps/star-omen

cd apps/star-omen
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
  python -m pytest -q tests/video_pipeline/package_review
```

This verifies SRT, manifest, no-replace publication, four review dimensions, preview command metadata, preview-media evidence schema and blocked/citable hermetic paths. It does not launch Stellarium, FFmpeg or ffprobe.

## 3. Create a fresh local smoke package

Stay in `apps/star-omen` and use one shell session:

```bash
export B9_RUN_ID="$(date -u '+%Y%m%dT%H%M%SZ')"
export B9_OUTPUT_DIR="data/generated_video_packages/july-21-local-smoke-${B9_RUN_ID}"
export B9_EVIDENCE_DIR="data/local_renderer_evidence/${B9_RUN_ID}"
mkdir -p data/generated_video_packages "$B9_EVIDENCE_DIR/screenshots"

PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import os
from pathlib import Path

from src.video_pipeline.vertical_package import publish_vertical_package
from tests.video_pipeline.package_review.test_vertical_package_e2e_v1 import july_build

_event, _result, _editorial, _script, build = july_build()
output = Path(os.environ["B9_OUTPUT_DIR"])
publish_vertical_package(output_dir=output, build=build)
print(output.resolve())
print(build.manifest.model_dump_json(indent=2))
PY
```

The package writer must fail rather than overwrite an existing directory. Do not remove an earlier package merely to make the command pass.

Required structured files:

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

`preview.mp4` is not a structured member and does not exist until the local preview command succeeds.

## 4. Verify the structured member inventory

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import json
import os
from pathlib import Path

root = Path(os.environ["B9_OUTPUT_DIR"])
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
for entry in manifest["members"]:
    path = root / entry["path"]
    raw = path.read_bytes()
    assert len(raw) == entry["byte_size"], entry["path"]
    assert hashlib.sha256(raw).hexdigest() == entry["sha256"], entry["path"]
print("manifest verification: PASS")
PY
```

Any changed member invalidates the package, review hashes and later renderer evidence.

## 5. Generate the bounded preview without a shell

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import json
import os
import subprocess
from pathlib import Path

root = Path(os.environ["B9_OUTPUT_DIR"])
payload = json.loads((root / "preview-command.json").read_text(encoding="utf-8"))
assert payload["shell"] is False
assert payload["output_path"] == "preview.mp4"
subprocess.run(
    payload["argv"],
    cwd=root,
    check=True,
    timeout=payload["timeout_seconds"],
    shell=False,
)
print((root / "preview.mp4").resolve())
PY
```

The expected preview is silent, 1080x1920, H.264, approximately 80 seconds, with readable ordered subtitles and zero audio streams. It is `preview.mp4`, never `final.mp4`.

## 6. Capture normalized ffprobe metadata

The evidence model does not launch ffprobe. Run ffprobe separately with only the fields accepted by the strict contract:

```bash
(
  cd "$B9_OUTPUT_DIR"
  ffprobe \
    -v error \
    -show_entries 'stream=index,codec_name,codec_type,width,height:format=filename,duration,size,format_name' \
    -of json \
    preview.mp4
) > "$B9_EVIDENCE_DIR/ffprobe-preview.json"

python -m json.tool "$B9_EVIDENCE_DIR/ffprobe-preview.json" >/dev/null
```

The JSON must identify exactly one 1080x1920 H.264 video stream, zero audio streams, an MP4 format, a finite duration in the accepted 80-second tolerance, filename `preview.mp4`, and a byte size matching the actual file.

## 7. Run and inspect the Stellarium script

Load the exact `$B9_OUTPUT_DIR/scene.ssc` in the installed Stellarium 26.x environment through its supported local script-loading workflow. Stellarium remains a renderer, not the scientific authority.

Verify visually:

- UTC matches `astronomy-event.json`;
- longitude, latitude and elevation match the observer;
- expected objects are selectable;
- tracking, time rate and GUI state are restored;
- no file, URL, include, eval, screenshot or shell command appears in the script.

Capture no more than 30 screenshots under:

```text
$B9_EVIDENCE_DIR/screenshots/
```

Do not add screenshots or media to the structured package directory.

## 8. Run the scientific and renderer hard gate

G6 cannot enter visual approval until the packaged astronomy has been recomputed through the verified offline provider and every supplied artifact/OCR check passes. Prepare normalized caller-supplied OCR observations:

```text
$B9_EVIDENCE_DIR/ocr-observations.json
```

The file is a JSON array of `OCRObservationV1` objects. OCR execution remains outside the evidence model; missing, reordered or clipped subtitles reject the gate.

Run:

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from skyfield_data import get_skyfield_data_path

from src.video_pipeline.asterisms import load_asterism_catalog
from src.video_pipeline.astronomy import (
    EphemerisFileSpecV1,
    SkyfieldEphemerisProvider,
    load_scientific_conventions,
)
from src.video_pipeline.assisted_review import (
    OCRObservationV1,
    RendererArtifactBindingV1,
    RendererReviewInputV1,
    build_renderer_hard_gate_report,
    canonical_renderer_hard_gate_bytes,
    canonical_renderer_review_input_bytes,
    verify_recomputed_astronomy,
    verify_renderer_artifacts,
)
from src.video_pipeline.contracts import AstronomyEventV1
from src.video_pipeline.local_sample import build_july_21_event

app = Path.cwd()
package = Path(os.environ["B9_OUTPUT_DIR"])
evidence = Path(os.environ["B9_EVIDENCE_DIR"])

def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()

ephemeris = Path(get_skyfield_data_path()) / "de421.bsp"
ephemeris_sha256 = digest(ephemeris)
provider = SkyfieldEphemerisProvider.from_local_ephemeris(
    ephemeris_path=ephemeris,
    ephemeris_spec=EphemerisFileSpecV1(
        logical_name="de421.bsp",
        expected_sha256=ephemeris_sha256,
        expected_size_bytes=ephemeris.stat().st_size,
        max_size_bytes=32 * 1024 * 1024,
    ),
    conventions=load_scientific_conventions(
        app / "data/video_pipeline/scientific_conventions_v1.yaml"
    ),
    catalog=load_asterism_catalog(
        app / "data/video_pipeline/asterism_catalog_v1.yaml"
    ),
)
packaged_event = AstronomyEventV1.model_validate_json(
    (package / "astronomy-event.json").read_text(encoding="utf-8")
)
recomputed_event = build_july_21_event(
    provider=provider,
    observer=packaged_event.observer,
    at_utc=packaged_event.peak_utc,
)
issues = verify_recomputed_astronomy(
    packaged=packaged_event,
    recomputed=recomputed_event,
)

manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
declared = [
    RendererArtifactBindingV1(path=item["path"], sha256=item["sha256"])
    for item in manifest["members"]
]
observed = [
    RendererArtifactBindingV1(path=item.path, sha256=digest(package / item.path))
    for item in declared
]
preview_sha256 = digest(package / "preview.mp4")
declared.append(
    RendererArtifactBindingV1(path="preview.mp4", sha256=preview_sha256)
)
observed.append(
    RendererArtifactBindingV1(path="preview.mp4", sha256=preview_sha256)
)
declared = sorted(declared, key=lambda item: item.path)
observed = sorted(observed, key=lambda item: item.path)

screenshots = sorted((evidence / "screenshots").glob("*.png"))
screenshot_sha256 = [digest(path) for path in screenshots]
ocr = [
    OCRObservationV1.model_validate(item)
    for item in json.loads(
        (evidence / "ocr-observations.json").read_text(encoding="utf-8")
    )
]
video_package = json.loads(
    (package / "video-package.json").read_text(encoding="utf-8")
)
issues.extend(
    verify_renderer_artifacts(
        declared_artifacts=declared,
        observed_artifacts=observed,
        declared_screenshot_sha256=screenshot_sha256,
        observed_screenshot_sha256=screenshot_sha256,
        ocr=ocr,
        expected_subtitles=[claim["text"] for claim in video_package["claims"]],
    )
)
review_input = RendererReviewInputV1(
    review_input_id=f"renderer-review-input:{os.environ['B9_RUN_ID'].lower()}",
    created_at=datetime.now(timezone.utc),
    artifacts=observed,
)
(evidence / "renderer-review-input.json").write_bytes(
    canonical_renderer_review_input_bytes(review_input)
)
report = build_renderer_hard_gate_report(
    review_input=review_input,
    issues=issues,
)
(evidence / "renderer-hard-gate.json").write_bytes(
    canonical_renderer_hard_gate_bytes(report)
)
if report.status != "passed":
    raise SystemExit(
        "renderer hard gate rejected: "
        + ",".join(item.code for item in report.issues)
    )
print("renderer hard gate: PASS")
PY
```

The old `3.25°` fixture, a placeholder ephemeris hash, missing OCR or any artifact drift must fail before visual approval.

## 9. Build media-bound local capability evidence

Record exact installed versions before building evidence:

```bash
export B9_FFMPEG_VERSION="$(ffmpeg -version | awk 'NR==1 {print $3}')"
# Set the exact installed 26.x semantic version reported by the local application.
export B9_STELLARIUM_VERSION="26.2.0"
```

Then build canonical evidence:

```bash
PYTHONPATH=../../packages/kb-contracts/python:../../packages/kb-text-core/python \
python - <<'PY'
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

from src.video_pipeline.capability import (
    ScreenshotEvidenceV1,
    build_local_capability_evidence,
    canonical_capability_evidence_bytes,
    inspect_preview_media_evidence,
)
from src.video_pipeline.preview import PreviewCapabilityV1, PreviewCommandV1
from src.video_pipeline.stellarium import StellariumScriptV1

package = Path(os.environ["B9_OUTPUT_DIR"])
evidence_root = Path(os.environ["B9_EVIDENCE_DIR"])
preview_command = PreviewCommandV1.model_validate_json(
    (package / "preview-command.json").read_text(encoding="utf-8")
)
preview_media = inspect_preview_media_evidence(
    path=package / "preview.mp4",
    ffprobe_payload=json.loads(
        (evidence_root / "ffprobe-preview.json").read_text(encoding="utf-8")
    ),
)
script_content = (package / "scene.ssc").read_text(encoding="utf-8")
script_sha = hashlib.sha256(script_content.encode("utf-8")).hexdigest()
script = StellariumScriptV1(
    script_id=f"stellarium-script:{script_sha[:32]}",
    event_id=json.loads((package / "astronomy-event.json").read_text())["event_id"],
    editorial_package_id=json.loads(
        (package / "editorial-package.json").read_text()
    )["editorial_package_id"],
    stellarium_version=os.environ["B9_STELLARIUM_VERSION"],
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
    sha256=script_sha,
)
capability = PreviewCapabilityV1(
    ffmpeg_version=os.environ["B9_FFMPEG_VERSION"],
    enabled_features=["lavfi-color", "subtitles", "libx264"],
    max_timeout_seconds=120,
)

screenshots = []
for path in sorted((evidence_root / "screenshots").glob("*.png")):
    raw = path.read_bytes()
    screenshots.append(
        ScreenshotEvidenceV1(
            path=path.relative_to(evidence_root).as_posix(),
            byte_size=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(),
        )
    )

record = build_local_capability_evidence(
    evidence_id=f"local-capability:macos-{os.environ['B9_RUN_ID'].lower()}",
    captured_at=datetime.now(timezone.utc),
    platform="macOS",
    architecture=platform.machine(),
    stellarium_script=script,
    preview_command=preview_command,
    preview_capability=capability,
    preview_media=preview_media,
    preview_observed=True,
    visual_review_status="approved",
    screenshots=screenshots,
)
out = evidence_root / "local-capability-evidence.json"
out.write_bytes(canonical_capability_evidence_bytes(record))
print(out.resolve())
PY
```

The command fails if the media bytes, ffprobe metadata, preview command, script, tool versions, screenshots or approval state are inconsistent.

## 10. Prepare the evidence handoff archive

Copy the exact non-structured media and package bindings into the evidence directory:

```bash
cp "$B9_OUTPUT_DIR/preview.mp4" "$B9_EVIDENCE_DIR/preview.mp4"
cp "$B9_OUTPUT_DIR/scene.ssc" "$B9_EVIDENCE_DIR/scene.ssc"
cp "$B9_OUTPUT_DIR/preview-command.json" "$B9_EVIDENCE_DIR/preview-command.json"
cp "$B9_OUTPUT_DIR/manifest.json" "$B9_EVIDENCE_DIR/package-manifest.json"

find "$B9_EVIDENCE_DIR/screenshots" -type f -name '*.png' -print0 \
  | sort -z \
  | xargs -0 shasum -a 256 \
  > "$B9_EVIDENCE_DIR/screenshot-sha256.txt"

tar -czf "data/b9-local-g6-evidence-${B9_RUN_ID}.tar.gz" \
  -C "$B9_EVIDENCE_DIR" \
  local-capability-evidence.json \
  renderer-review-input.json \
  renderer-hard-gate.json \
  ocr-observations.json \
  ffprobe-preview.json \
  preview.mp4 \
  scene.ssc \
  preview-command.json \
  package-manifest.json \
  screenshot-sha256.txt \
  screenshots
```

The archive must not include `.env`, keys, corpus files, Qdrant data, private absolute paths or unrelated machine logs.

## 11. Failure handling

- Existing output directory: choose a new run ID; never overwrite or delete it as part of this workflow.
- Structured hash mismatch: preserve the failed evidence separately and rebuild a fresh package.
- FFmpeg failure or timeout: record no approved capability evidence.
- ffprobe mismatch: do not edit metadata; investigate or regenerate the preview.
- Scientific recomputation or hard-gate rejection: do not show or accept visual approval; preserve the rejected report and rebuild from source-backed inputs.
- Stellarium version/capability mismatch: keep G6 blocked.
- Missing screenshot or visual rejection: `visual_review_status` cannot be approved.
- Any corpus, ingest, collection or production-Qdrant activity: stop immediately.

A successful local preview does not authorize publishing and does not convert blocked classical evidence into a quotation. B9 is complete only after the evidence archive is independently verified and the final B9 closeout is merged.
