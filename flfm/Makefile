.PHONY: all

secret.key:
	@set -e; bash -c "base64 -d <(openssl genrsa | sed -rn '/(-{5}[\w|\s]*-{5})/{p};n;p') > secret.key"

all: secret.key
