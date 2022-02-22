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
)

type flagOptions struct {
	Scheme     string
	Host       string
	Auth       string
	Subcommand string
	Slug       string
	Products
	After    string
	Before   string
	StdOut   bool
	OutFile  string
	Endpoint string
	Timeout  int
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
	case "grid":
		log.Println("Initiating 'grid' command")
		if len(co.Products) == 0 {
			fmt.Fprintf(os.Stderr, "error::No products provided\n")
			flag.PrintDefaults()
		} else if co.Slug == "" {
			fmt.Fprintf(os.Stderr, "error::Please provide a slug for the watershed\n")
			os.Exit(1)
		}
		dss, err := grid(&co, &url)
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
		os.Stdout.WriteString(dss)
	case "extract":
		if co.Slug == "" {
			fmt.Fprintf(os.Stderr, "error::Please provide a slug for the watershed\n")
			os.Exit(1)
		}
		log.Println("Initiating 'extract' command")
		extract(&co, &url)
	case "get":
		if co.Endpoint == "" {
			fmt.Fprintf(os.Stderr, "error::No endpoint provided\n")
			os.Exit(1)
		}
		log.Println("Initiating 'endpoint' command")
		url.Path = co.Endpoint
		b, err := getResponseBody(url.String())
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
		}
		if co.StdOut {
			os.Stdout.WriteString(string(b))
		}
	}

}

func (co *flagOptions) addFlagOptions() {
	t2 := time.Now().UTC()
	// t2.Truncate(24 * time.Hour)
	t1 := t2.AddDate(0, 0, -7)

	flag.StringVar(&co.Scheme, "scheme", "https", "URL scheme; default=https")
	flag.StringVar(&co.Host, "host", "localhost", "URL host; default=localhost")
	flag.StringVar(&co.Auth, "auth", "", "Authorization Token")
	flag.StringVar(&co.Subcommand, "sub", "", "Subcommands: extract, grid, and get")
	flag.StringVar(&co.After, "after", t1.Format(time.RFC3339), "After time (StartTime UTC); default=now-7 days")
	flag.StringVar(&co.Before, "before", t2.Format(time.RFC3339), "Before time (EndTime UTC); default=now")
	flag.StringVar(&co.OutFile, "out", "", "Output file and location")
	flag.BoolVar(&co.StdOut, "stdout", false, "Send output to stdout; default=false")
	flag.StringVar(&co.Slug, "slug", "", "Watershed slug")
	flag.Var(&co.Products, "product", "Product List; --product value --product value --product value...")
	flag.StringVar(&co.Endpoint, "endpoint", "", "Get response body from endpoint")
	flag.IntVar(&co.Timeout, "timeout", 300, "Grid download timeout (sec); default=300")
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
