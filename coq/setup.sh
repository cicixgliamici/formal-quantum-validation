#!/usr/bin/env bash
# Run inside an initialized opam switch; never change the caller's global switch.
set -euo pipefail
cd "$(dirname "$0")/.."
source coq/toolchain.env
test "$(ocamlc -version)" = "$OCAML_VERSION"
opam repository add coq-released https://coq.inria.fr/opam/released --yes
opam install --yes "coq.$COQ_VERSION" "coq-quantumlib.$QUANTUMLIB_VERSION"
if [ ! -d build/SQIR/.git ]; then
  git clone https://github.com/inQWIRE/SQIR.git build/SQIR
fi
git -C build/SQIR fetch origin "$SQIR_REVISION"
git -C build/SQIR checkout --detach "$SQIR_REVISION"
test "$(git -C build/SQIR rev-parse HEAD)" = "$SQIR_REVISION"
# Refuse locally edited semantic sources; ignore only checkout line endings.
git -c core.filemode=false -C build/SQIR diff --ignore-space-at-eol --exit-code HEAD -- SQIR/SQIR.v SQIR/UnitarySem.v
# Only these two upstream modules are in our dependency closure. Building them
# directly avoids pulling unrelated VOQC/example dependencies into the backend.
opam exec -- coqc -R build/SQIR/SQIR SQIR build/SQIR/SQIR/SQIR.v
opam exec -- coqc -R build/SQIR/SQIR SQIR build/SQIR/SQIR/UnitarySem.v
