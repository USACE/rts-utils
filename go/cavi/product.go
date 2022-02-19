package main

import (
	"encoding/json"
	"time"

	"github.com/google/uuid"
)

type productInfo struct {
	ID                 uuid.UUID   `json:"id"`
	Slug               string      `json:"slug"`
	Tags               []uuid.UUID `json:"tags"`
	Name               string      `json:"name"`
	TemporalResolution int         `json:"temporal_resolution"`
	TemporalDuration   int         `json:"temporal_duration"`
	DssFpart           string      `json:"dss_fpart"`
	ParameterID        uuid.UUID   `json:"parameter_id"`
	Parameter          string      `json:"parameter"`
	UnitID             uuid.UUID   `json:"unit_id"`
	Unit               string      `json:"unit"`
	Description        string      `json:"description"`
	SuiteID            uuid.UUID   `json:"suite_id"`
	Suite              string      `json:"suite"`
	Label              string      `json:"label"`
	After              *time.Time  `json:"after"`
	Before             *time.Time  `json:"before"`
	ProductfileCount   int         `json:"productfile_count"`
}

// Product Info Map
type productMap map[string]productInfo

// getProductMap
// String argument, URL, and receiver
// Return error
func (p productMap) getProductMap(u string) error {
	b, err := getResponseBody(u)
	if err != nil {
		return err
	}
	pis := []productInfo{}
	if err = json.Unmarshal(b, &pis); err != nil {
		return err
	}
	for _, pi := range pis {
		p[pi.Slug] = pi
	}
	return nil
}
