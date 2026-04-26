package main

import (
	"context"
	"fmt"
	"os"

	"github.com/moustafattia/yoyopod-core/workers/voice/go/internal/provider"
	"github.com/moustafattia/yoyopod-core/workers/voice/go/internal/worker"
)

func main() {
	if err := worker.New(provider.MockProvider{}, os.Stdin, os.Stdout, os.Stderr).Run(context.Background()); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
