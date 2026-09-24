package main

import (
	"strings"

	"github.com/pkg/errors"
)

var allowableHosts = map[string]bool{
	"cumulus.cwbi.mil":                true,
	"localhost":                       true,
	"cumulus-api.corps.cloud":         true,
	"develop-cumulus-api.corps.cloud": true,
	"water-api.corps.cloud":           true,
	"develop-water-api.corps.cloud":   true,
	"cumulus-api.rsgis.dev":           true,
	"develop-cumulus-api.rsgis.dev":   true,
	"water-api.rsgis.dev":             true,
	"develop-water-api.rsgis.dev":     true,
	"github.com":                      true,
	"raw.githubusercontent.com":       true,
}

func allowableHost(s string) error {
	b, ok := allowableHosts[s]
	if !ok || !b {
		return errors.New("not an allowable host")
	}
	return nil
}

// apiEndpoint keeps legacy hosts unchanged and accepts both old and already
// prefixed endpoint strings from the Cumulus Python library.
func apiEndpoint(host, endpoint string) string {
	if host != "cumulus.cwbi.mil" {
		return endpoint
	}
	endpoint = strings.TrimLeft(endpoint, "/")
	return "api/" + strings.TrimPrefix(endpoint, "api/")
}
