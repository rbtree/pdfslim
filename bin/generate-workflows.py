#!/usr/bin/env python3
"""
Generate PDF Slim Service bundles.

The full bash worker is embedded into each workflow's Run Shell Script action,
so the .workflow bundle is the only runtime artifact (no separate worker file).

Run:    python3 bin/generate-workflows.py
"""

from __future__ import annotations

import plistlib
import shutil
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "quick-actions"

VARIANTS = [
    {
        "menu_name": "PDF Slim - Light (Print, 300dpi)",
        "preset": "light",
        "gs_setting": "/printer",
        "bundle_id": "rs.rbt.pdfslim.quickaction.light",
    },
    {
        "menu_name": "PDF Slim - Medium (eBook, 150dpi)",
        "preset": "medium",
        "gs_setting": "/ebook",
        "bundle_id": "rs.rbt.pdfslim.quickaction.medium",
    },
]

# Worker script. Placeholders __PRESET__ / __GS_SETTING__ are substituted at
# generation time. Everything else is plain bash and stays as-is at runtime.
SCRIPT_TEMPLATE = r"""set -euo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

PRESET="__PRESET__"
GS_SETTING="__GS_SETTING__"

if ! command -v gs >/dev/null 2>&1; then
    /usr/bin/osascript -e 'display alert "PDF Slim" message "Ghostscript is required but not installed.\n\nInstall with:\n    brew install ghostscript\n\nThen try again."' >/dev/null 2>&1 || true
    exit 1
fi

exit_code=0
for input in "$@"; do
    case "$input" in
        *.pdf|*.PDF) ;;
        *) echo "skip (not a PDF): $input" >&2; continue ;;
    esac
    [ -f "$input" ] || { echo "skip (missing): $input" >&2; continue; }

    base="${input%.[pP][dD][fF]}"
    output="${base}_${PRESET}.pdf"

    if ! gs -sDEVICE=pdfwrite \
            -dCompatibilityLevel=1.4 \
            -dPDFSETTINGS="$GS_SETTING" \
            -dNOPAUSE -dQUIET -dBATCH \
            -sOutputFile="$output" \
            "$input"; then
        echo "compression failed: $input" >&2
        exit_code=1
        continue
    fi

    orig=$(stat -f%z "$input")
    new=$(stat -f%z "$output")
    pct=$(awk "BEGIN{printf \"%.1f\", ($orig-$new)/$orig*100}")
    orig_mb=$(awk "BEGIN{printf \"%.2f\", $orig/1024/1024}")
    new_mb=$(awk "BEGIN{printf \"%.2f\", $new/1024/1024}")
    printf '%s: %s MB -> %s MB (%s%% saved)\n' \
        "$(basename "$input")" "$orig_mb" "$new_mb" "$pct"
done
exit "$exit_code"
"""


def make_script(preset: str, gs_setting: str) -> str:
    return (
        SCRIPT_TEMPLATE
        .replace("__PRESET__", preset)
        .replace("__GS_SETTING__", gs_setting)
    )


def new_uuid() -> str:
    return str(uuid.uuid4()).upper()


def run_shell_script_action(script: str) -> dict:
    return {
        "isViewVisible": True,
        "action": {
            "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
            "ActionName": "Run Shell Script",
            "ActionParameters": {
                "COMMAND_STRING": script,
                "CheckedForUserDefaultShell": True,
                "inputMethod": 1,
                "shell": "/bin/bash",
                "source": "",
            },
            "AMAccepts": {
                "Container": "List",
                "Optional": True,
                "Types": ["com.apple.cocoa.string"],
            },
            "AMActionVersion": "2.0.3",
            "AMApplication": ["Automator"],
            "AMParameterProperties": {
                "COMMAND_STRING": {},
                "CheckedForUserDefaultShell": {},
                "inputMethod": {},
                "shell": {},
                "source": {},
            },
            "AMProvides": {
                "Container": "List",
                "Types": ["com.apple.cocoa.string"],
            },
            "BundleIdentifier": "com.apple.RunShellScript",
            "CFBundleVersion": "2.0.3",
            "CanShowSelectedItemsWhenRun": False,
            "CanShowWhenRun": True,
            "Category": ["AMCategoryUtilities"],
            "Class Name": "RunShellScriptAction",
            "InputUUID": new_uuid(),
            "Keywords": ["Shell", "Script", "Command", "Run", "Unix"],
            "OutputUUID": new_uuid(),
            "UUID": new_uuid(),
            "UnlocalizedApplications": ["Automator"],
            "arguments": {
                "0": {"default value": 0,  "name": "inputMethod",                "required": "0", "type": "0", "uuid": "0"},
                "1": {"default value": "", "name": "COMMAND_STRING",             "required": "0", "type": "0", "uuid": "1"},
                "2": {"default value": "/bin/sh", "name": "shell",               "required": "0", "type": "0", "uuid": "2"},
                "3": {"default value": False, "name": "CheckedForUserDefaultShell", "required": "0", "type": "0", "uuid": "3"},
                "4": {"default value": "", "name": "source",                     "required": "0", "type": "0", "uuid": "4"},
            },
            "isViewVisible": True,
            "location": "309.000000:316.000000",
        },
    }


def workflow_plist(preset: str, gs_setting: str) -> dict:
    return {
        "AMApplicationBuild": "522",
        "AMApplicationVersion": "2.10",
        "AMDocumentVersion": "2",
        "actions": [run_shell_script_action(make_script(preset, gs_setting))],
        "connectors": {},
        "workflowMetaData": {
            "serviceApplicationBundleID": "com.apple.finder",
            "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
            "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": 0,
            "useAutomaticInputType": 1,
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
        },
    }


def info_plist(menu_name: str, bundle_id: str) -> dict:
    return {
        "CFBundleDevelopmentRegion": "en_US",
        "CFBundleIdentifier": bundle_id,
        "CFBundleName": menu_name,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": "1.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "10.10",
        "NSServices": [
            {
                "NSMenuItem": {"default": menu_name},
                "NSMessage": "runWorkflowAsService",
                "NSRequiredContext": {"NSApplicationIdentifier": "com.apple.finder"},
                "NSSendFileTypes": ["com.adobe.pdf"],
            }
        ],
    }


def write_bundle(menu_name: str, preset: str, gs_setting: str, bundle_id: str) -> Path:
    bundle = OUT_DIR / f"{menu_name}.workflow"
    contents = bundle / "Contents"
    if bundle.exists():
        shutil.rmtree(bundle)
    contents.mkdir(parents=True)

    with open(contents / "Info.plist", "wb") as f:
        plistlib.dump(info_plist(menu_name, bundle_id), f)

    with open(contents / "document.wflow", "wb") as f:
        plistlib.dump(workflow_plist(preset, gs_setting), f)

    return bundle


def main() -> None:
    # Wipe the build-output directory so renamed bundles don't linger.
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    for v in VARIANTS:
        bundle = write_bundle(v["menu_name"], v["preset"], v["gs_setting"], v["bundle_id"])
        print(f"wrote {bundle.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
