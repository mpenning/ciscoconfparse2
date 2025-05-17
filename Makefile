DOCHOST ?= $(shell bash -c 'read -p "documentation host: " dochost; echo $$dochost')

# dynamic ciscoconfparse2 VERSION detection (via version str in pyproject.toml)
#
# - at this point, I prefer printing in perl to set shell variables...
#   - open './pyproject.toml' as $pyproject
#   - loop over each line, assigned to $line
#   - If we see the version string in a line, print it and end
export VERSION := $(shell hatch version )


# We must escape Makefile dollar signs as $$foo...
export PING_STATUS := $(shell perl -e '@output = qx/ping -q -W0.5 -c1 4.2.2.2/; $$alloutput = join "", @output; if ( $$alloutput =~ /\s0\sreceived/ ) { print "failure"; } else { print "success"; }')

export NUMBER_OF_CCP_TESTS := $(shell grep "def " tests/test*py | wc -l)

# Makefile color codes...
#     ref -> https://stackoverflow.com/a/5947802/667301
COL_GREEN=\033[0;32m
COL_CYAN=\033[0;36m
COL_YELLOW=\033[0;33m
COL_RED=\033[0;31m
COL_END=\033[0;0m

.DEFAULT_GOAL := test

# Ref -> https://stackoverflow.com/a/26737258/667301
# Ref -> https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/
.PHONY: dep
dep:
	@echo "$(COL_GREEN)>> getting ciscoconfparse2 pypi artifacts (wheel and tar.gz)$(COL_END)"
	pip install -U pip
	# Delete bogus files... see https://stackoverflow.com/a/73992288/667301
	perl -e 'unlink( grep { /^\W\d*\.*\d*/ && !-d } glob( "*" ) );'

.PHONY: build
build:
	# Build a new wheel / src_dist from scratch
	-rm -rf dist/
	hatch build

.PHONY: install_build
install_build:
	make build
	# Install the newly-built package
	pip install --force-reinstall dist/*.tar.gz

.PHONY: cicd
cicd:
	@echo "$(COL_CYAN)>> Use CI/CD to publish ciscoconfparse2 pypi artifacts$(COL_END)"
	make clean
	-git commit --all -m "chore: commit changes I forgot before running 'make cicd'"
	# yamlfix doesn't understand pyproject.toml config
	#     if used in pre-commit...
	yamlfix .github/workflows/
	-git commit --all -m "chore: yamlfix changes"
	# Run pre-commit on all files... ignore failures, which should be auto-fixed
	-pre-commit run -a
	-git commit --all -m "chore: pre-commit changes"
	# upgrade packaging infra and ciscoconfparse2 dependencies...
	make dep
	-git commit --all -m "Version $$VERSION"
	# tag the repo with $$VERSION, upon git tag push,
	# this triggers .github/workflows/cicd-publish.yml
	-git tag $$VERSION
	git checkout main
	git merge @{-1}           # Merge the previous branch
	git push origin main
	# push tag to github origin, which triggers a github CICD action (see above)
	-git push origin $$VERSION
	git checkout develop
	git pull origin main

.PHONY: bump-version-patch
bump-version-patch:
	$(shell python dev_tools/git_helper.py -I patch)

.PHONY: bump-version-minor
bump-version-minor:
	$(shell python dev_tools/git_helper.py -I minor)


.PHONY: repo-push
repo-push:
	@echo "$(COL_GREEN)>> git push and merge (w/o force) to ciscoconfparse2 main branch to github$(COL_END)"
	make ping
	-git checkout master || git checkout main # Add dash to ignore checkout fails
	# Now the main branch is checked out...
	THIS_BRANCH=$(shell git branch --show-current)  # assign 'main' to $THIS_BRANCH
	git merge @{-1}                           # merge the previous branch into main...
	git push origin $(THIS_BRANCH)            # git push to origin / $THIS_BRANCH
	git checkout @{-1}                        # checkout the previous branch...


.PHONY: repo-push-force
repo-push-force:
	@echo "$(COL_GREEN)>> git push and merge (w/ force) ciscoconfparse2 local main branch to github$(COL_END)"
	make ping
	-git checkout master || git checkout main # Add dash to ignore checkout fails
	# Now the main branch is checked out...
	THIS_BRANCH=$(shell git branch --show-current)  # assign 'main' to $THIS_BRANCH
	git merge @{-1}                           # merge the previous branch into main...
	git push --force-with-lease origin $(THIS_BRANCH)    # force push to origin / $THIS_BRANCH
	git checkout @{-1}                        # checkout the previous branch...

.PHONY: repo-push-tag
repo-push-tag:
	@echo "$(COL_GREEN)>> git push (w/ local tag) ciscoconfparse2 local main branch to github$(COL_END)"
	git push origin +main
	git push --tags origin +main

.PHONY: repo-push-tag-force
repo-push-tag-force:
	@echo "$(COL_GREEN)>> git push (w/ local tag and w/ force) ciscoconfparse2 local main branch to github$(COL_END)"
	git push --force-with-lease origin +main
	git push --force-with-lease --tags origin +main

.PHONY: pylama
pylama:
	@echo "$(COL_GREEN)>> running pylama against ciscoconfparse2$(COL_END)"
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylama --ignore=E501,E301,E265,E266 ciscoconfparse2/*py | less -XR

.PHONY: pylint
pylint:
	@echo "$(COL_GREEN)>> running pylint against ciscoconfparse2$(COL_END)"
	# Good usability info here -> https://pythonspeed.com/articles/pylint/
	pylint --rcfile=./utils/pylintrc --ignore-patterns='^build|^dist|utils/pylintrc|README.rst|CHANGES|LICENSE|MANIFEST.in|Makefile|TODO' --output-format=colorized * | less -XR

.PHONY: tutorial
tutorial:
	@echo ">> building the ciscoconfparse2 tutorial"
	rst2html5 --jquery --reveal-js --pretty-print-code --embed-stylesheet --embed-content --embed-images tutorial/ccp_tutorial.rst > tutorial/ccp_tutorial.html

.PHONY: parse-ios
parse-ios:
	cd tests; python parse_test.py 1 | less -XR

.PHONY: parse-ios-factory
parse-ios-factory:
	cd tests; python parse_test.py 2 | less -XR

.PHONY: parse-ios-banner
parse-iosxr-banner:
	cd tests; python parse_test.py 3 | less -XR

.PHONY: perf-acl
perf-acl:
	cd tests; python performance_case.py 5 | less -XR

.PHONY: perf-factory-intf
perf-factory-intf:
	cd tests; python performance_case.py 6 | less -XR

.PHONY: flake
flake:
	flake8 --ignore E501,E226,E225,E221,E303,E302,E265,E128,E125,E124,E41,W291 --max-complexity 10 ciscoconfparse2 | less

.PHONY: coverage-pytest
coverage-pytest:
	@echo "[[[ py.test Coverage ]]]"
	cd tests;py.test --cov-report term-missing --cov=ciscoconfparse2.py -s -v

.PHONY: pydocstyle
pydocstyle:
	# Run a numpy-style doc checker against all files matching ciscoconfparse2/*py
	find ciscoconfparse2/*py | xargs -I{} pydocstyle --convention=numpy {}

.PHONY: doctest
doctest:
	# Run the doc tests
	cd sphinx-doc; make doctest

.PHONY: rm-timestamp
rm-timestamp:
	@echo "$(COL_GREEN)>> delete .pip_dependency if older than a day$(COL_END)"
	#delete .pip_dependency if older than a day
	$(shell find .pip_dependency -mtime +1 -exec rm {} \;)

.PHONY: timestamp
timestamp:
	@echo "$(COL_GREEN)>> Create .pip_dependency$(COL_END)"
	$(shell touch .pip_dependency)

.PHONY: ping
ping:
	@echo "$(COL_GREEN)>> ping to ensure internet connectivity$(COL_END)"
	@if [ "$${PING_STATUS}" = 'success' ]; then return 0; else return 1; fi

.PHONY: test
test:
	@echo "$(COL_GREEN)>> running unit tests$(COL_END)"
	$(shell touch .pip_dependency)
	make timestamp
	#make ping
	make clean
	# You can also test with verbose output:
	#     cd tests && pytest -vvs ./test_*py
	cd tests && pytest ./test_*py

.PHONY: coverage
coverage:
	@echo "$(COL_GREEN)>> running unit tests$(COL_END)"
	$(shell touch .pip_dependency)
	make timestamp
	#make ping
	make clean
	# run tests with coverage (ensure you run 'make dep' before)
	cd tests && coverage run -m pytest test*py
	# Move the coverage file to the base git directory
	cd tests && mv .coverage ../

.PHONY: clean
clean:
	@echo "$(COL_GREEN)>> cleaning the repo$(COL_END)"
	# Delete bogus files... see https://stackoverflow.com/a/73992288/667301
	perl -e 'unlink( grep { /^=\d*\.*\d*/ && !-d } glob( "*" ) );'
	find ./* -name '*.pyc' -exec rm {} \;
	find ./* -name '*.so' -exec rm {} \;
	find ./* -name '*.coverage' -exec rm {} \;
	find ./* -name '*.cover' -exec rm {} \;
	-find ./* -name '.pytest_cache' -exec rm -rf {} \;
	@# A minus sign prefixing the line means it ignores the return value
	-find ./* -path '*__pycache__' -exec rm -rf {} \;
	@# remove all the MockSSH keys
	-find ./* -name '*.key' -exec rm {} \;
	-rm .pip_dependency
	-rm -rf .mypy_cache/
	-rm -rf .pytest_cache/
	-rm -rf .eggs/
	-rm -rf .cache/
	-rm -rf build/ dist/ ciscoconfparse2.egg-info/ setuptools*
	-rm -rf artifacts/

.PHONY: help
help:
	@# An @ sign prevents outputting the command itself to stdout
	@echo "help                 : You figured that out ;-)"
	@echo "cicd                 : Git commit, build the project w/ CICD, and push to pypi"
	@echo "repo-push            : Build the project and push to github"
	@echo "test                 : Run all doctests and unit tests"
	@echo "dev                  : Get all dependencies for the dev environment"
	@echo "dep                  : Get all prod dependencies"
	@echo "devtest              : Run tests - Specific to Mike Pennington's build env"
	@echo "coverage             : Run tests with coverage - Specific to this build env"
	@echo "flake                : Run PyFlake code audit w/ McCabe complexity"
	@echo "clean                : Housecleaning"
	@echo "parse-ios            : Parse configs/sample_01.ios with default args"
	@echo "parse-ios-factory    : Parse configs/sample_01.ios with factory=True"
	@echo "parse-iosxr-banner   : Parse an interesting IOSXR banner"
	@echo "perf-acl             : cProfile configs/sample_05.ios (100 acls)"
	@echo "perf-factory-intf    : cProfile configs/sample_06.ios (many intfs, factory=True)"
	@echo ""
