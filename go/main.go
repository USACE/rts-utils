package main

import (
	"bufio"
	"bytes"
	"flag"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"path"
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

func main() {
	// scheme default=https
	// host e.g., develop-water-api.rsgis.dev
	// endpoint e.g., watersheds
	// After time
	// Before time
	// file output default= system temp

	// id := uuid.New()
	// outfile := os.TempDir() + id.String()

	t2 := time.Now()
	t2.Truncate(24 * time.Hour)
	t1 := t2.AddDate(0, 0, -7)

	scheme := flag.String("scheme", "https", "Scheme used")
	host := flag.String("host", "", "Host name")
	endpoint := flag.String("endpoint", "", "Endpoint")
	tAfter := flag.String("after", t1.Format(time.RFC3339), "After time (StartTime)")
	tBefore := flag.String("before", t2.Format(time.RFC3339), "Before time (EndTime)")
	fpOut := flag.String("out", "", "Output file and location")
	stdOut := flag.Bool("stdout", false, "Send output to stdout")

	flag.Parse()
	// args := flag.Args()

	// Check if some flags have values
	if len(*host) == 0 {
		panic("No host defined")
	}
	if len(*endpoint) == 0 {
		panic("No endpoint defined")
	}

	// Try to parse the times provided
	after, err := time.Parse(time.RFC3339, *tAfter)
	if err != nil {
		log.Fatalln(err)
	}
	after.Truncate(24 * time.Hour)

	before, err := time.Parse(time.RFC3339, *tBefore)
	if err != nil {
		log.Fatalln(err)
	}
	before.Truncate(24 * time.Hour)

	url := url.URL{
		Scheme: *scheme,
		Host:   *host,
		Path:   *endpoint,
	}
	q := url.Query()
	q.Set("after", *tAfter)
	q.Set("before", *tBefore)
	url.RawQuery = q.Encode()

	// Call the service function to get the resulting body
	// service(url.String())
	req, err := http.NewRequest("GET", url.String(), nil)
	if err != nil {
		log.Fatalln(err)
	}

	req.Header.Set("Accept", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		log.Fatalln(err)
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
		if *stdOut {
			os.Stdout.WriteString(string(line))
		}

	}
	// Get the output path and check the path
	if *fpOut != "" {
		fpDir := path.Dir(*fpOut)
		if info, err := os.Stat(fpDir); info.IsDir() {
			os.WriteFile(*fpOut, buffer.Bytes(), 0644)
		} else {
			log.Fatalln(err)
		}
	}

}
