package main

import (
	"encoding/json"

	"github.com/google/uuid"
)

type watershed struct {
	ID           uuid.UUID `json:"id"`
	OfficeSymbol string    `json:"office_symbol"`
	Slug         string    `json:"slug"`
	Name         string    `json:"name"`
	AreaGroups   []string  `json:"area_groups"`
	BoundingBox  []int     `json:"bbox"`
}

// Watershed Map type
type watershedMap map[string]watershed

// getWatershedMap
// String argument, URL, and receiver
// Return error
func (w watershedMap) getWatershedMap(u string) error {
	b, err := getResponseBody(u)
	if err != nil {
		return err
	}
	wss := []watershed{}
	if err = json.Unmarshal(b, &wss); err != nil {
		return err
	}
	for _, ws := range wss {
		w[ws.Slug] = ws
	}
	return nil
}
