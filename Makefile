IMAGE := schinckel/xmltv-mutator

.PHONY: release

requirements.txt: poetry.lock pyproject.toml
	poetry export -o requirements.txt

bump-major:
	cat VERSION | awk -F. '{print $$1 + 1 ".0.0"}' | tee VERSION

bump-minor:
	cat VERSION | awk -F. '{print $$1 "." $$2 + 1  ".0"}' | tee VERSION

VERSION: app.py requirements.txt
	cat VERSION | awk -F. '{print $$1 "." $$2 "." $$3 + 1}' | tee VERSION

release: Dockerfile VERSION
	docker buildx build . -t $(IMAGE):armv6 --platform linux/arm/v6 --push
	docker buildx build . -t $(IMAGE):armv7 --platform linux/arm/v7 --push
	docker buildx build . -t $(IMAGE):amd64 --platform linux/amd64 --push
	docker buildx build . -t $(IMAGE):arm64 --platform linux/arm64 --push

	docker pull $(IMAGE):armv6
	docker pull $(IMAGE):armv7
	docker pull $(IMAGE):amd64
	docker pull $(IMAGE):arm64

	docker image rm --force $(IMAGE):latest

	docker manifest create $(IMAGE):latest \
		$(IMAGE):armv6 \
		$(IMAGE):armv7 \
		$(IMAGE):amd64 \
		$(IMAGE):arm64 \
		--amend

	docker manifest annotate $(IMAGE):latest $(IMAGE):armv6 --variant v6l
	docker manifest annotate $(IMAGE):latest $(IMAGE):armv7 --variant v7l

	docker manifest create $(IMAGE):$(shell cat VERSION) \
		$(IMAGE):armv6 \
		$(IMAGE):armv7 \
		$(IMAGE):amd64 \
		$(IMAGE):arm64 \
		--amend

	docker manifest annotate $(IMAGE):$(shell cat VERSION) $(IMAGE):armv6 --variant v6l
	docker manifest annotate $(IMAGE):$(shell cat VERSION) $(IMAGE):armv7 --variant v7l

	docker manifest push $(IMAGE):$(shell cat VERSION)
	docker manifest push $(IMAGE):latest
