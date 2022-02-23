package main

import (
	"encoding/json"
	"fmt"
	"reflect"
	"strconv"
)

func (o *flagOptions) UnmarshalJSON(data []byte) error {
	var m map[string]interface{}

	// unmarshal to map[]interface{}
	if err := json.Unmarshal(data, &m); err != nil {
		return err
	}
	// convert to bool and remove key
	if so, ok := m["StdOut"]; ok {
		b, err := strconv.ParseBool(so.(string))
		if err != nil {
			return err
		}
		o.StdOut = b
		delete(m, "StdOut")
	}

	for k, v := range m {
		err := SetField(o, k, v)
		if err != nil {
			return err
		}
	}
	return nil
}

func SetField(obj interface{}, name string, value interface{}) error {
	structValue := reflect.ValueOf(obj).Elem()
	structFieldValue := structValue.FieldByName(name)

	if !structFieldValue.IsValid() {
		return fmt.Errorf("no such field: %s in obj", name)
	}

	if !structFieldValue.CanSet() {
		return fmt.Errorf("cannot set %s field value", name)
	}

	structFieldType := structFieldValue.Type()
	val := reflect.ValueOf(value)
	if structFieldType != val.Type() {
		return fmt.Errorf("provided value %s type didn't match obj field type", name)
	}

	structFieldValue.Set(val)
	return nil
}
