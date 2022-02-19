package main

import (
	"log"
	"net/url"
	"time"

	"github.com/pkg/errors"
)

func grid(f *flagOptions, url *url.URL) (string, error) {
	slug := f.Slug
	products := f.Products
	tAfter := f.After
	tBefore := f.Before
	// stdOut := f.StdOut
	timeoutSec := f.Timeout
	auth := f.Auth

	var dssfilepath string

	// Map the watersheds from Cumulus and check we have it
	wm := make(watershedMap)
	url.Path = "watersheds"
	if err := wm.getWatershedMap(url.String()); err != nil {
		return dssfilepath, err
	} else {
		log.Println("Created watershed Go mapping from Cumulus")
	}

	// Get the watershed we asked for
	ws := wm[slug]
	if ws.Slug == "" {
		return dssfilepath, errors.Errorf("Slug '%s' not found\n", ws.Slug)
	} else {
		log.Println("Watershed:", ws.Name)
	}

	// Map the products from Cumulus and check we have what we want
	pm := make(productMap)
	url.Path = "products"
	if err := pm.getProductMap(url.String()); err != nil {
		return dssfilepath, err
	} else {
		log.Println("Created products Go mapping from Cumulus")
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
		return dssfilepath, errors.Errorf("Product list is empty\n")
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
	if err := us.postPayload(url.String(), p, auth); err != nil {
		return dssfilepath, err
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
				return dssfilepath, err
			}
			log.Println("File downloaded to:", fn)
			dssfilepath := "dssfile::" + string(fn)
			return dssfilepath, nil
		} else {
			time.Sleep(1 * time.Second)
		}
	}

	return dssfilepath, errors.New("No grids produced")
}
