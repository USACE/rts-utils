package main

import "github.com/pkg/errors"

var allowableHosts = map[string]bool{
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
