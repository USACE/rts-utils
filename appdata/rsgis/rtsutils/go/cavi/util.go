package main

import "github.com/pkg/errors"

var allowableHosts = map[string]bool{
	"localhost":                       true,
	"localhost:90035":                 true,
	"cumulus-api.corps.cloud":         true,
	"develop-cumulus-api.corps.cloud": true,
	"water-api.corps.cloud":           true,
	"develop-water-api.corps.cloud":   true,
	"cumulus-api.rsgis.dev":           true,
	"develop-cumulus-api.rsgis.dev":   true,
	"water-api.rsgis.dev":             true,
	"develop-water-api.rsgis.dev":     true,
}

func allowableHost(s string) error {
	b, ok := allowableHosts[s]
	if !ok || !b {
		return errors.New("not an allowable host")
	}
	return nil
}

// func (o *flagOptions) UnmarshalJSON(data []byte) error {
// 	var m map[string]interface{}

// 	// unmarshal to map[]interface{}
// 	if err := json.Unmarshal(data, &m); err != nil {
// 		return err
// 	}
// 	// convert to bool and remove key for StdOut
// 	if so, ok := m["StdOut"]; ok {
// 		b, err := strconv.ParseBool(so.(string))
// 		if err != nil {
// 			return err
// 		}
// 		o.StdOut = b
// 		delete(m, "StdOut")
// 	}

// 	for k, v := range m {
// 		err := SetField(o, k, v)
// 		if err != nil {
// 			return err
// 		}
// 	}
// 	return nil
// }

// func SetField(obj interface{}, name string, value interface{}) error {
// 	structValue := reflect.ValueOf(obj).Elem()
// 	structFieldValue := structValue.FieldByName(name)

// 	if !structFieldValue.IsValid() {
// 		return fmt.Errorf("no such field: %s in obj", name)
// 	}

// 	if !structFieldValue.CanSet() {
// 		return fmt.Errorf("cannot set %s field value", name)
// 	}

// 	structFieldType := structFieldValue.Type()
// 	val := reflect.ValueOf(value)
// 	if structFieldType != val.Type() {
// 		return fmt.Errorf("provided value %s type didn't match obj field type", name)
// 	}

// 	structFieldValue.Set(val)
// 	return nil
// }
