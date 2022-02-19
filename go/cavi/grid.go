package main

import (
	"fmt"
	"log"
	"net/url"
	"os"
	"time"
)

func grid(f *flagOptions, url *url.URL) {
	slug := f.Slug
	products := f.Products
	tAfter := f.After
	tBefore := f.Before
	stdOout := f.StdOut
	timeoutSec := f.Timeout

	// Map the watersheds from Cumulus and check we have it
	wm := make(watershedMap)
	url.Path = "watersheds"
	if err := wm.getWatershedMap(url.String()); err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
		os.Exit(1)
	} else {
		log.Println("Created watershed map from Cumulus")
	}

	// Get the watershed we asked for
	ws := wm[slug]
	if ws.Slug == "" {
		fmt.Fprintf(os.Stderr, "Slug '%s' not found", ws.Slug)
		os.Exit(1)
	} else {
		log.Println("Watershed:", ws.Name)
	}

	// Map the products from Cumulus and check we have what we want
	pm := make(productMap)
	url.Path = "products"
	if err := pm.getProductMap(url.String()); err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
	} else {
		log.Println("Created products map from Cumulus")
	}

	productIDs := []string{}
	for _, product := range products {
		for k, v := range pm {
			if k == product {
				// fmt.Println(v.Name, "exists")
				productIDs = append(productIDs, v.ID.String())
			}
		}
	}
	if len(productIDs) == 0 {
		fmt.Fprintf(os.Stderr, "Error - Product list is empty")
		os.Exit(1)
	}

	// Populate the payload struct before sending off
	p := payload{
		After:       tAfter,
		Before:      tBefore,
		WatershedID: ws.ID.String(),
		ProductID:   productIDs,
	}

	var us updateStatus
	url.Path = "downloads"
	if err := us.postPayload(url.String(), p); err != nil {
		fmt.Fprintf(os.Stderr, "Error - %s", err)
		os.Exit(1)
	} else {
		log.Println("Download ID:", us.ID)
	}

	url.Path = "downloads/" + us.ID

	timeout := time.Duration(int(time.Second) * timeoutSec)
	var fn filename
	for start := time.Now(); time.Since(start) < timeout; {
		us.getStatus(url.String())
		log.Printf("ID: %s\tStatus: %s\tProgress: %d\tFile: %s", us.ID, us.Status, us.Progress, us.File)
		if us.Status == "SUCCESS" && us.Progress >= 100 && us.File != "" {
			if err := fn.downloadDss(us.File, ""); err != nil {
				fmt.Fprintf(os.Stderr, "Error - %s", err)
			}
			log.Println("File downloaded to:", fn)
			break
		} else {
			time.Sleep(1 * time.Second)
		}
	}
	if stdOout {
		os.Stdout.WriteString("dssfile::" + string(fn))
	}
}
