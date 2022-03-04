package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"time"
)

const (
	usage = `error::
usage: %s

Options:
`
	authserver = "http://localhost:50123"
)

type flagOptions struct {
	ID         string
	Scheme     string
	Host       string
	Auth       string
	Subcommand string
	After      string
	Before     string
	Endpoint   string
	Timeout    float64
	Products
}

type Products []string

func main() {
	var co flagOptions
	co.addFlagOptions()

	// Get some stdin
	stat, _ := os.Stdin.Stat()
	if (stat.Mode() & os.ModeCharDevice) == 0 {
		data, err := ioutil.ReadAll(os.Stdin)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
		if err = json.Unmarshal(data, &co); err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
	}

	// need to check the allowable hosts
	if err := allowableHost(co.Host); err != nil {
		fmt.Fprintf(os.Stderr, "error::%s\n", err)
		os.Exit(1)
	}

	// Basic URL and check service available
	url := url.URL{
		Scheme: co.Scheme,
		Host:   co.Host,
	}

	if _, err := checkService(url.String()); err != nil {
		fmt.Fprintf(os.Stderr, "error::%s\n", err)
		os.Exit(1)
	} else {
		log.Println("Service up:", url.String())
	}

	switch co.Subcommand {
	case "git":
		// not do all the git stuff
		fmt.Println()
	case "grid":
		log.Println("Initiating 'grid' command")
		if len(co.Products) == 0 {
			fmt.Fprintf(os.Stderr, "error::No products provided\n")
			flag.PrintDefaults()
		} else if co.ID == "" {
			fmt.Fprintf(os.Stderr, "error::Please provide a UUID for the watershed\n")
			os.Exit(1)
		}

		// get auth token
		auth, err := getResponseBody(authserver)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
		}
		co.Auth = string(auth)

		url.Path = co.Endpoint

		p := payload{
			After:       co.After,
			Before:      co.Before,
			WatershedID: co.ID,
			ProductID:   co.Products,
		}
		dss, err := grid(url, p, int(co.Timeout), co.Auth)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
		os.Stdout.WriteString(dss)
	case "extract":
		if co.Endpoint == "" {
			fmt.Fprintf(os.Stderr, "error::Please provide a slug for the watershed\n")
			os.Exit(1)
		}
		log.Println("Initiating 'extract' command")

		q := url.Query()
		q.Set("after", co.After)
		q.Set("before", co.Before)
		url.RawQuery = q.Encode()
		url.Path = co.Endpoint

		log.Printf("URL: %s", url.String())

		extract(url)
	case "get":
		if co.Endpoint == "" {
			fmt.Fprintf(os.Stderr, "error::no endpoint provided\n")
			os.Exit(1)
		}
		log.Println("Initiating 'endpoint' command")
		url.Path = co.Endpoint
		b, err := getResponseBody(url.String())
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
		}
		os.Stdout.WriteString(string(b))
	}

}

func (co *flagOptions) addFlagOptions() {
	t2 := time.Now().UTC()
	// t2.Truncate(24 * time.Hour)
	t1 := t2.AddDate(0, 0, -7)

	flag.StringVar(&co.Scheme, "id", "", "UUID")
	flag.StringVar(&co.Scheme, "scheme", "https", "URL scheme; default=https")
	flag.StringVar(&co.Host, "host", "localhost", "URL host; default=localhost")
	flag.StringVar(&co.Auth, "auth", "", "Authorization Token")
	flag.StringVar(&co.Subcommand, "sub", "", "Subcommands: extract, grid, and get")
	flag.StringVar(&co.After, "after", t1.Format(time.RFC3339), "After time (StartTime UTC); default=now-7 days")
	flag.StringVar(&co.Before, "before", t2.Format(time.RFC3339), "Before time (EndTime UTC); default=now")
	flag.Var(&co.Products, "product", "Product List; --product value --product value --product value...")
	flag.StringVar(&co.Endpoint, "endpoint", "", "Get response body from endpoint")
	flag.Float64Var(&co.Timeout, "timeout", 300, "Grid download timeout (sec); default=300")

	flag.Usage = func() {
		fmt.Fprintf(flag.CommandLine.Output(), usage, os.Args[0])
		flag.PrintDefaults()
	}
	flag.Parse()
}

func (p *Products) String() string {
	return "warning::No products provided"
}
func (p *Products) Set(v string) error {
	*p = append(*p, v)
	return nil
}
