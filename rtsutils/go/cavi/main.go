package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
)

const (
	usage = `error::
usage: %s

Options:
`
	// authserver = "https://localhost:50123"
)

type flagOptions struct {
	Version    bool
	ID         string
	Scheme     string
	Host       string
	Auth       string
	Subcommand string
	After      string
	Before     string
	Endpoint   string
	Branch     string
	Path       string
	Timeout    float64
	Products
}

type Products []string

func main() {
	var co flagOptions
	co.addFlagOptions()
	if co.Version {
		fmt.Println(helperVersion)
		return
	}
	executable, _ := os.Executable()
	fmt.Fprintf(os.Stderr, "%s\nHelper: %s\n", helperVersion, executable)

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
	co.Host = strings.TrimSpace(co.Host)
	if err := allowableHost(co.Host); err != nil {
		fmt.Fprintf(os.Stderr, "error::Host %q is not allowed. For CWBI use Host=cumulus.cwbi.mil and Scheme=https, without /api in Host.\n", co.Host)
		os.Exit(1)
	}
	apiToken = ""
	if co.Host == "cumulus.cwbi.mil" {
		if co.Scheme != "https" {
			fmt.Fprintln(os.Stderr, "error::CWBI requires Scheme=https")
			os.Exit(1)
		}
		apiToken = strings.TrimSpace(strings.TrimPrefix(co.Auth, "Bearer "))
	}

	// Basic URL and check service available
	url := url.URL{
		Scheme: co.Scheme,
		Host:   co.Host,
	}

	// API requests must not depend on the separate website/login root working.
	if co.Subcommand != "get" && co.Subcommand != "grid" {
		resp, err := checkService(url.String())
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
		resp.Body.Close()
	}

	switch co.Subcommand {
	case "git":
		// not do all the git stuff
		log.Println("Initiating 'git' command")
		url.Path = co.Endpoint
		ref := plumbing.NewBranchReferenceName(co.Branch)
		err := goGitRepo(url.String(), "origin", ref, co.Path)

		if err == git.NoErrAlreadyUpToDate {
			log.Println("Repository " + err.Error())
			os.Exit(0)
		}
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
	case "grid":
		log.Println("Initiating 'grid' command")
		if co.Host == "cumulus.cwbi.mil" && apiToken == "" {
			fmt.Fprintln(os.Stderr, "error::CWBI downloads require CAC authentication. Install the accompanying rtsutils/go Python files and restart RTS.")
			os.Exit(1)
		}
		if len(co.Products) == 0 {
			fmt.Fprintf(os.Stderr, "error::No products provided\n")
			flag.PrintDefaults()
		} else if co.ID == "" {
			fmt.Fprintf(os.Stderr, "error::Please provide a UUID for the watershed\n")
			os.Exit(1)
		}

		// get auth token
		// auth, err := getAuth(authserver)
		// if err != nil {
		// 	log.Printf("error::Auth server not running")
		// } else {
		// 	log.Printf("Auth: authenticated")
		// 	co.Auth = string(auth)
		// }

		url.Path = apiEndpoint(co.Host, co.Endpoint)

		p := payload{
			// Request body is unchanged for authenticated downloads.
			After:       co.After,
			Before:      co.Before,
			WatershedID: co.ID,
			ProductID:   co.Products,
		}
		log.Printf("%s", p)
		if co.Host == "cumulus.cwbi.mil" {
			url.Path = "api/downloads"
		}
		log.Printf("%s", url.String())
		dss, err := grid(url, p, int(co.Timeout))
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
		url.Path = apiEndpoint(co.Host, co.Endpoint)
		b, err := getResponseBody(url.String())
		if err != nil {
			fmt.Fprintf(os.Stderr, "error::%s\n", err)
			os.Exit(1)
		}
		os.Stdout.WriteString(string(b))
	}

}

func (co *flagOptions) addFlagOptions() {
	flag.BoolVar(&co.Version, "version", false, "Print helper build version without connecting")
	t2 := time.Now().UTC()
	// t2.Truncate(24 * time.Hour)
	t1 := t2.AddDate(0, 0, -7)

	flag.StringVar(&co.ID, "id", "", "UUID")
	flag.StringVar(&co.Scheme, "scheme", "https", "URL scheme; default=https")
	flag.StringVar(&co.Host, "host", "localhost", "URL host; default=localhost")
	flag.StringVar(&co.Auth, "auth", "", "Authorization Token")
	flag.StringVar(&co.Subcommand, "sub", "", "Subcommands: extract, grid, and get")
	flag.StringVar(&co.After, "after", t1.Format(time.RFC3339), "After time (StartTime UTC); default=now-7 days")
	flag.StringVar(&co.Before, "before", t2.Format(time.RFC3339), "Before time (EndTime UTC); default=now")
	flag.Var(&co.Products, "product", "Product List; --product value --product value --product value...")
	flag.StringVar(&co.Endpoint, "endpoint", "", "Get response body from endpoint")
	flag.StringVar(&co.Branch, "branch", "", "GitHub repository branch name")
	flag.StringVar(&co.Path, "path", "", "Path to target repository")
	flag.Float64Var(&co.Timeout, "timeout", 600, "Grid download timeout (sec); default=600")

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
