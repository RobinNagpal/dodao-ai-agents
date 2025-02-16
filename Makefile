build-docs:
	mdbook build docs

deploy-docs:
	aws s3 sync docs/book s3://docs.koalagains.com --acl public-read
	aws cloudfront create-invalidation --distribution-id E31MRQCK388MVB --paths "/*"
