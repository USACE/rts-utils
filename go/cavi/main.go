package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type flagOptions struct {
	Host    string
	Scheme  string
	OutFile string
	StdOut  bool
	After   string
	Before  string
	Slug    string
	Timeout int
	Products
}

type Products []string

func main() {
	var co flagOptions
	cmdLine := flag.NewFlagSet("", flag.ExitOnError)
	subcommands := []string{"extract", "grid"}
	cmdLine.Usage = func() {
		_, f := filepath.Split(os.Args[0])
		fmt.Fprintf(os.Stderr, "Usage of %s:\n\nSubcommands: %s\n\n", f, strings.Join(subcommands, ", "))
		cmdLine.PrintDefaults()
		os.Exit(1)
	}

	if len(os.Args) == 1 {
		fmt.Fprintf(os.Stderr, "No arguments provided\n")
		cmdLine.Usage()
	}

	co.addFlagOptions(cmdLine)
	cmdLine.Parse(os.Args[2:])

	// Get some stdin
	stat, _ := os.Stdin.Stat()
	if (stat.Mode() & os.ModeCharDevice) == 0 {
		data, err := ioutil.ReadAll(os.Stdin)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error - %s", err)
			os.Exit(1)
		}
		if err = json.Unmarshal(data, &co); err != nil {
			fmt.Fprintf(os.Stderr, "Error - %s", err)
			os.Exit(1)
		}
	}

	// Basic URL and check service available
	url := url.URL{
		Scheme: co.Scheme,
		Host:   co.Host,
	}
	if _, err := checkService(url.String()); err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
		os.Exit(1)
	} else {
		log.Println("Service up:", url.String())
	}

	fmt.Printf("%+v\n", &co)

	switch os.Args[1] {
	case "grid":
		log.Println("Initiating 'grid' command")
		if len(co.Products) == 0 {
			fmt.Fprintf(os.Stderr, "Error - No products provided\n")
			cmdLine.Usage()
		} else if co.Slug == "" {
			fmt.Fprintf(os.Stderr, "Error - Please provide a slug for the watershed\n")
			os.Exit(1)
		}
		grid(&co, &url)
	case "extract":
		if co.Slug == "" {
			fmt.Fprintf(os.Stderr, "Error - Please provide a slug for the watershed\n")
			os.Exit(1)
		}
		log.Println("Initiating 'extract' command")
		extract(&co, &url)
	case "-h", "--help", "help":
		cmdLine.Usage()
	default:
		fmt.Fprintf(os.Stderr, "Error - Expecting either 'grid' or 'extract'; %s provided", os.Args[1])
		os.Exit(1)
	}

}

func (co *flagOptions) addFlagOptions(f *flag.FlagSet) {
	t2 := time.Now().UTC()
	// t2.Truncate(24 * time.Hour)
	t1 := t2.AddDate(0, 0, -7)
	f.StringVar(&co.Host, "host", "localhost", "")
	f.StringVar(&co.Scheme, "scheme", "http", "")
	f.StringVar(&co.After, "after", t1.Format(time.RFC3339), "After time (StartTime)")
	f.StringVar(&co.Before, "before", t2.Format(time.RFC3339), "Before time (EndTime)")
	f.StringVar(&co.OutFile, "out", "", "Output file and location")
	f.BoolVar(&co.StdOut, "stdout", false, "Send output to stdout")
	f.StringVar(&co.Slug, "slug", "", "Watershed slug")
	f.Var(&co.Products, "product", "Product List; --product value --product value --product value...")
	f.IntVar(&co.Timeout, "timeout", 300, "Grid download timeout (sec) default is 300 sec")
}

func (p *Products) String() string {
	return `{"message": "Products"}`
}
func (p *Products) Set(v string) error {
	*p = append(*p, v)
	return nil
}
