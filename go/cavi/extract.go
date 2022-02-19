package main

import (
	"bufio"
	"bytes"
	"fmt"
	"io"
	"log"
	"net/url"
	"os"
	"path"
	"strings"
	"time"

	"github.com/google/uuid"
)

const endpoint string = "watersheds/:slug/extract"

type Site struct {
	SiteNumber  string      `json:"site_number"`
	Code        string      `json:"code"`
	SiteID      uuid.UUID   `json:"site_id"`
	ParameterID uuid.UUID   `json:"paramter_id"`
	Times       []time.Time `json:"times"`
	Values      []float64   `json:"values"`
}

func extract(f *flagOptions, url *url.URL) {
	url.Path = strings.Replace(endpoint, ":slug", f.Slug, 1)

	tAfter := f.After
	tBefore := f.Before
	stdOut := f.StdOut
	fpOut := f.OutFile

	q := url.Query()
	q.Set("after", tAfter)
	q.Set("before", tBefore)
	url.RawQuery = q.Encode()

	log.Printf("URL: %s", url.String())

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
		if stdOut {
			os.Stdout.WriteString(string(line))
		}

	}
	// Get the output path and check the path
	if fpOut != "" {
		fpDir := path.Dir(fpOut)
		if info, err := os.Stat(fpDir); info.IsDir() {
			os.WriteFile(fpOut, buffer.Bytes(), 0644)
		} else {
			log.Fatalln(err)
		}
	}

}
