package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"net/url"
	"os"
	"time"

	"github.com/google/uuid"
)

type Site struct {
	SiteNumber  string      `json:"site_number"`
	Code        string      `json:"code"`
	SiteID      uuid.UUID   `json:"site_id"`
	ParameterID uuid.UUID   `json:"paramter_id"`
	Times       []time.Time `json:"times"`
	Values      []float64   `json:"values"`
}

func extract(url url.URL) {

	resp, err := getResponse(url.String())
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	reader := bufio.NewReader(resp.Body)
	buffer := &bytes.Buffer{}

	for {
		line, err := reader.ReadBytes('\n')
		if err == io.EOF {
			break
		}
		line = bytes.TrimSpace(line)
		buffer.Write(line)
		os.Stdout.WriteString(string(line))
	}
}
