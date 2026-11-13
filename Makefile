# Convenience targets for the Linux host. All commands are python3 / POSIX.
# Contract: docs/08. Nothing here starts real hardware.
PY ?= python3
export PYTHONPATH := $(CURDIR)/src:$(CURDIR):$(CURDIR)/integration$(if $(PYTHONPATH),:$(PYTHONPATH),)
export PYTHONUTF8 := 1

.PHONY: help bootstrap check doctor smoke fairness probe dist docker-check

help:
	@echo "make bootstrap    # ./deploy/bootstrap.sh"
	@echo "make check        # contract tests + fairness audit + smoke + probe"
	@echo "make doctor       # environment report (add STRICT=1 for CI)"
	@echo "make probe        # backend factory + real-hardware guard demo"
	@echo "make dist         # build the Linux tarball in dist/"
	@echo "make docker-check # run contract tests inside the container image"

bootstrap:
	./deploy/bootstrap.sh

check:
	$(PY) scripts/contract_tests.py
	$(PY) scripts/run_smoke.py
	$(PY) scripts/fairness_audit.py
	$(PY) scripts/run_backend_probe.py

doctor:
	$(PY) deploy/doctor.py $(if $(STRICT),--strict,)

smoke:
	$(PY) scripts/run_smoke.py

fairness:
	$(PY) scripts/fairness_audit.py

probe:
	$(PY) scripts/run_backend_probe.py

dist:
	$(PY) deploy/make_dist.py

docker-check:
	docker compose --profile default run --rm pasd python3 scripts/contract_tests.py
